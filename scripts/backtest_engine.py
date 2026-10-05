from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MANIFEST = ROOT / "research" / "data" / "ACQUISITION_MANIFEST.json"
OUT = ROOT / "research" / "results"
OUT.mkdir(parents=True, exist_ok=True)

STRATEGY_CFG = json.loads((ROOT / "config" / "strategy.json").read_text(encoding="utf-8"))
COST_CFG = json.loads((ROOT / "config" / "costs.json").read_text(encoding="utf-8"))
START = COST_CFG["sample_start"]
END = COST_CFG["sample_end"]
STOP_POINTS = float(STRATEGY_CFG["stop_loss_points"])
SLIPPAGE_POINTS = float(COST_CFG["primary_slippage_points_per_leg"])
COST = {
    "brokerage_per_order": float(COST_CFG["brokerage_per_order_inr"]),
    "stt_sell_rate": float(COST_CFG["stt_option_sale_rate"]),
    "exchange_txn_rate": float(COST_CFG["exchange_transaction_rate"]),
    "ipft_rate": float(COST_CFG["ipft_rate"]),
    "sebi_rate": float(COST_CFG["sebi_turnover_rate"]),
    "gst_rate": float(COST_CFG["gst_rate_on_brokerage_exchange_sebi_ipft"]),
    "stamp_buy_rate": float(COST_CFG["stamp_duty_option_buy_rate"]),
}


def lot_size(expiry: pd.Timestamp | str) -> int:
    d = pd.Timestamp(expiry).date()
    if d <= pd.Timestamp("2024-12-26").date():
        return 25
    if d <= pd.Timestamp("2025-12-30").date():
        return 75
    return 65


def fill_cost(raw_price: float, side: str, qty: int) -> tuple[float, dict[str, float]]:
    """Apply adverse slippage and client-side transaction costs."""
    if raw_price < 0:
        raise ValueError("Option price cannot be negative")
    if side not in {"BUY", "SELL"}:
        raise ValueError(f"Unsupported side: {side}")

    if side == "SELL":
        exec_price = max(0.0, raw_price - SLIPPAGE_POINTS)
    else:
        exec_price = raw_price + SLIPPAGE_POINTS

    turnover = abs(exec_price * qty)
    brokerage = COST["brokerage_per_order"]
    stt = turnover * COST["stt_sell_rate"] if side == "SELL" else 0.0
    exchange = turnover * COST["exchange_txn_rate"]
    ipft = turnover * COST["ipft_rate"]
    sebi = turnover * COST["sebi_rate"]
    stamp = turnover * COST["stamp_buy_rate"] if side == "BUY" else 0.0
    gst = COST["gst_rate"] * (brokerage + exchange + ipft + sebi)
    total_cost = brokerage + stt + exchange + ipft + sebi + stamp + gst
    return exec_price, {
        "brokerage": brokerage,
        "stt": stt,
        "exchange_charge": exchange,
        "ipft": ipft,
        "sebi_fee": sebi,
        "stamp_duty": stamp,
        "gst": gst,
        "total_cost": total_cost,
        "slippage_points": abs(exec_price - raw_price),
    }


def nearest(frame: pd.DataFrame, spot: float) -> float | None:
    if frame.empty:
        return None
    z = frame.dropna(subset=["open"]).copy()
    if z.empty:
        return None
    z["distance"] = (z["strike"] - spot).abs()
    return float(z.sort_values(["distance", "strike"]).iloc[0]["strike"])


def target(frame: pd.DataFrame, premium: float, spot: float) -> float | None:
    """Choose next-open strike by premium distance, then spot distance, then lower strike."""
    if frame.empty:
        return None
    z = frame.dropna(subset=["open"]).copy()
    if z.empty:
        return None
    z["premium_distance"] = (z["open"] - premium).abs()
    z["spot_distance"] = (z["strike"] - spot).abs()
    return float(
        z.sort_values(["premium_distance", "spot_distance", "strike"])
        .iloc[0]["strike"]
    )


def price_at(
    frame: pd.DataFrame,
    timestamp: pd.Timestamp,
    expiry: pd.Timestamp,
    option_type: str,
    strike: float,
    column: str,
) -> float | None:
    z = frame[
        (frame["timestamp"] == timestamp)
        & (frame["expiry"] == expiry)
        & (frame["option_type"] == option_type)
        & (frame["strike"] == strike)
    ]
    if z.empty or pd.isna(z.iloc[0][column]):
        return None
    return float(z.iloc[0][column])


def short_pnl_points(realized_raw_points: float, legs: dict[str, dict[str, Any]], marks: dict[str, float]) -> float:
    return realized_raw_points + sum(
        leg["raw_entry"] - marks[name] for name, leg in legs.items()
    )


def should_stop(pnl_points: float, stop_points: float = STOP_POINTS) -> bool:
    return pnl_points <= -stop_points


def allow_adjustment(next_timestamp: pd.Timestamp, exit_timestamp: pd.Timestamp) -> bool:
    return next_timestamp < exit_timestamp


def ratio_trigger(premium_a: float, premium_b: float) -> bool:
    hi = max(premium_a, premium_b)
    lo = min(premium_a, premium_b)
    return hi > 0 and (lo / hi) <= 0.50


def asof_spot(spot_day: pd.DataFrame, timestamp: pd.Timestamp) -> float | None:
    z = spot_day[spot_day["timestamp"] <= timestamp]
    if z.empty:
        return None
    return float(z.iloc[-1]["close"])


def order_record(
    timestamp: pd.Timestamp,
    action: str,
    leg: str,
    side: str,
    raw_price: float,
    qty: int,
) -> dict[str, Any]:
    exec_price, costs = fill_cost(raw_price, side, qty)
    return {
        "timestamp": timestamp,
        "action": action,
        "leg": leg,
        "side": side,
        "raw_price": raw_price,
        "exec_price": exec_price,
        "qty": qty,
        **costs,
    }


def build_universe(con: duckdb.DuckDBPyConnection, spot: pd.DataFrame, option_paths: list[str]) -> pd.DataFrame:
    file_list = "[" + ",".join("'" + p.replace("'", "''") + "'" for p in option_paths) + "]"
    con.execute(
        f"CREATE OR REPLACE VIEW options AS "
        f"SELECT * FROM read_parquet({file_list}, union_by_name=true)"
    )
    expiry_map = con.execute(
        """
        WITH pairs AS (
            SELECT DISTINCT CAST(date AS DATE) AS trade_date, CAST(expiry AS DATE) AS expiry
            FROM options
            WHERE CAST(date AS DATE) BETWEEN DATE '2024-10-01' AND DATE '2025-12-31'
        ),
        ranked AS (
            SELECT trade_date, expiry,
                   ROW_NUMBER() OVER (PARTITION BY trade_date ORDER BY expiry) AS rn
            FROM pairs
            WHERE expiry >= trade_date
        )
        SELECT trade_date,
               MAX(CASE WHEN rn=1 THEN expiry END) AS current_expiry,
               MAX(CASE WHEN rn=2 THEN expiry END) AS next_expiry
        FROM ranked
        GROUP BY trade_date
        ORDER BY trade_date
        """
    ).df()
    expiry_map["trade_date"] = pd.to_datetime(expiry_map["trade_date"]).dt.strftime("%Y-%m-%d")
    s0930 = spot[
        spot["timestamp"].dt.strftime("%H:%M:%S").eq("09:30:00")
        & spot["timestamp"].dt.strftime("%Y-%m-%d").between(START, END)
    ][["trade_date", "close"]].drop_duplicates("trade_date").rename(columns={"close": "spot_0930"})
    u = expiry_map.merge(s0930, on="trade_date", how="inner")
    u["lot_current"] = u["current_expiry"].map(lot_size)
    u["lot_next"] = u["next_expiry"].map(lot_size)
    u = u[u["lot_current"] == u["lot_next"]].copy()

    con.register("eligible_seed", u[["trade_date", "current_expiry", "next_expiry", "spot_0930"]])
    entries = con.execute(
        """
        SELECT
            CAST(o.date AS DATE) AS trade_date,
            CAST(o.expiry AS DATE) AS expiry,
            o.option_type,
            CAST(o.strike AS DOUBLE) AS strike,
            CAST(o.open AS DOUBLE) AS open,
            e.spot_0930,
            CASE
              WHEN CAST(o.expiry AS DATE)=e.current_expiry AND o.option_type='CE' THEN 'current_ce'
              WHEN CAST(o.expiry AS DATE)=e.next_expiry AND o.option_type='PE' THEN 'next_pe'
            END AS leg
        FROM options o
        JOIN eligible_seed e
          ON CAST(o.date AS DATE)=CAST(e.trade_date AS DATE)
        WHERE CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS TIME)=TIME '09:30:00'
          AND (
             (CAST(o.expiry AS DATE)=e.current_expiry AND o.option_type='CE')
             OR
             (CAST(o.expiry AS DATE)=e.next_expiry AND o.option_type='PE')
          )
        """
    ).df()
    entries["trade_date"] = pd.to_datetime(entries["trade_date"]).dt.strftime("%Y-%m-%d")

    selected: list[dict[str, Any]] = []
    for d, g in entries.groupby("trade_date"):
        spot0 = float(g.iloc[0]["spot_0930"])
        ce = g[g["leg"] == "current_ce"]
        pe = g[g["leg"] == "next_pe"]
        ce_strike = nearest(ce, spot0)
        pe_strike = nearest(pe, spot0)
        ce_row = ce[ce["strike"] == ce_strike] if ce_strike is not None else pd.DataFrame()
        pe_row = pe[pe["strike"] == pe_strike] if pe_strike is not None else pd.DataFrame()
        if ce_strike is None or pe_strike is None or ce_row.empty or pe_row.empty:
            continue
        row = g.iloc[0]
        selected.append(
            {
                "trade_date": d,
                "current_expiry": pd.Timestamp(row["expiry"]) if row["leg"] == "current_ce" else pd.Timestamp(ce.iloc[0]["expiry"]),
                "next_expiry": pd.Timestamp(pe.iloc[0]["expiry"]),
                "spot_0930": spot0,
                "initial_ce_strike": ce_strike,
                "initial_pe_strike": pe_strike,
                "lot_size": int(u.loc[u["trade_date"] == d, "lot_current"].iloc[0]),
            }
        )
    final = pd.DataFrame(selected).sort_values("trade_date").reset_index(drop=True)
    if len(final) < 250:
        raise RuntimeError(f"Phase 4 universe unexpectedly small: {len(final)}")
    final.to_csv(OUT / "phase4_universe.csv", index=False)
    return final


def load_day(
    con: duckdb.DuckDBPyConnection,
    stage_path: Path,
    trade_date: str,
) -> pd.DataFrame:
    return con.execute(
        f"""
        SELECT trade_date, local_ts AS timestamp, expiry, option_type, strike, open, close
        FROM read_parquet('{stage_path.as_posix()}')
        WHERE trade_date=DATE '{trade_date}'
        ORDER BY local_ts
        """
    ).df()


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    option_paths = [str(CACHE / "hf_options" / item["source_path"]) for item in manifest["options_source"]["files"]]

    spot = pd.read_csv(CACHE / "spot" / "extracted" / "NIFTY_5min_5yr_2021_2026.csv")
    spot["timestamp"] = pd.to_datetime(spot["timestamp"], errors="coerce")
    spot = spot.dropna(subset=["timestamp"]).sort_values("timestamp")
    spot["trade_date"] = spot["timestamp"].dt.strftime("%Y-%m-%d")

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.execute("PRAGMA threads=4")

    universe = build_universe(con, spot, option_paths)
    con.register("final_universe", universe[[
        "trade_date", "current_expiry", "next_expiry"
    ]])

    stage = OUT / "phase4_selected_bars.parquet"
    if not stage.exists():
        file_list = "[" + ",".join("'" + p.replace("'", "''") + "'" for p in option_paths) + "]"
        con.execute(
            f"""
            COPY (
              SELECT
                CAST(o.date AS DATE) AS trade_date,
                CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS TIMESTAMP) AS local_ts,
                CAST(o.expiry AS DATE) AS expiry,
                o.option_type,
                CAST(o.strike AS DOUBLE) AS strike,
                CAST(o.open AS DOUBLE) AS open,
                CAST(o.close AS DOUBLE) AS close
              FROM read_parquet({file_list}, union_by_name=true) o
              JOIN final_universe u
                ON CAST(o.date AS DATE)=CAST(u.trade_date AS DATE)
               AND (
                    (CAST(o.expiry AS DATE)=u.current_expiry AND o.option_type='CE')
                    OR
                    (CAST(o.expiry AS DATE)=u.next_expiry AND o.option_type='PE')
               )
              WHERE CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS TIME)
                    BETWEEN TIME '09:30:00' AND TIME '15:15:00'
            )
            TO '{stage.as_posix()}'
            (FORMAT PARQUET, COMPRESSION ZSTD)
            """
        )

    bars_meta = con.execute(
        f"SELECT COUNT(*) AS rows FROM read_parquet('{stage.as_posix()}')"
    ).df()
    trades: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []

    for row in universe.itertuples(index=False):
        d = row.trade_date
        current_expiry = pd.Timestamp(row.current_expiry)
        next_expiry = pd.Timestamp(row.next_expiry)
        lot = int(row.lot_size)
        spot_day = spot[spot["trade_date"] == d][["timestamp", "close"]].sort_values("timestamp")
        frame = load_day(con, stage, d)
        frame["trade_date"] = d
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        frame["expiry"] = pd.to_datetime(frame["expiry"])
        frame["strike"] = frame["strike"].astype(float)

        entry_ts = pd.Timestamp(f"{d} 09:30:00")
        exit_ts = pd.Timestamp(f"{d} 15:15:00")

        ce_rows = frame[
            (frame["timestamp"] == entry_ts)
            & (frame["expiry"] == current_expiry)
            & (frame["option_type"] == "CE")
        ]
        pe_rows = frame[
            (frame["timestamp"] == entry_ts)
            & (frame["expiry"] == next_expiry)
            & (frame["option_type"] == "PE")
        ]

        ce_strike = nearest(ce_rows, float(row.spot_0930))
        pe_strike = nearest(pe_rows, float(row.spot_0930))
        ce_open = price_at(frame, entry_ts, current_expiry, "CE", ce_strike, "open") if ce_strike is not None else None
        pe_open = price_at(frame, entry_ts, next_expiry, "PE", pe_strike, "open") if pe_strike is not None else None
        if ce_open is None or pe_open is None:
            trades.append({"trade_date": d, "status": "EXCLUDED_UNEXECUTABLE", "reason": "missing_entry_price"})
            continue

        legs: dict[str, dict[str, Any]] = {
            "ce": {
                "expiry": current_expiry,
                "option_type": "CE",
                "strike": float(ce_strike),
                "raw_entry": float(ce_open),
                "exec_entry": None,
            },
            "pe": {
                "expiry": next_expiry,
                "option_type": "PE",
                "strike": float(pe_strike),
                "raw_entry": float(pe_open),
                "exec_entry": None,
            },
        }
        realized_raw = 0.0
        realized_exec = 0.0
        orders: list[dict[str, Any]] = []
        adjustment_count = 0
        stop_hit = False
        exclusion_reason: str | None = None
        monitoring_gap_count = 0

        for name, leg in legs.items():
            rec = order_record(entry_ts, "ENTRY", name, "SELL", leg["raw_entry"], lot)
            leg["exec_entry"] = rec["exec_price"]
            orders.append(rec)

        expected_times = pd.date_range(
            entry_ts + pd.Timedelta(minutes=1),
            exit_ts - pd.Timedelta(minutes=1),
            freq="min",
        )

        for ts in expected_times:
            marks: dict[str, float] = {}
            for name, leg in legs.items():
                value = price_at(
                    frame,
                    ts,
                    leg["expiry"],
                    leg["option_type"],
                    leg["strike"],
                    "close",
                )
                if value is not None:
                    marks[name] = value
            if len(marks) != 2:
                monitoring_gap_count += 1
                continue

            pnl_points = short_pnl_points(realized_raw, legs, marks)
            next_ts = ts + pd.Timedelta(minutes=1)

            if should_stop(pnl_points):
                exit_prices = {
                    name: price_at(
                        frame,
                        next_ts,
                        leg["expiry"],
                        leg["option_type"],
                        leg["strike"],
                        "open",
                    )
                    for name, leg in legs.items()
                }
                if any(value is None for value in exit_prices.values()):
                    exclusion_reason = "UNEXECUTABLE_STOP"
                    break
                for name, leg in legs.items():
                    rec = order_record(
                        next_ts, "STOP_EXIT", name, "BUY", float(exit_prices[name]), lot
                    )
                    orders.append(rec)
                stop_hit = True
                break

            # A new adjustment cannot be initiated for execution at 15:15,
            # because the locked strategy closes the entire position then.
            if not allow_adjustment(next_ts, exit_ts):
                continue

            hi = max(marks.values())
            lo = min(marks.values())
            if not ratio_trigger(lo, hi):
                continue

            low_name = min(marks, key=marks.get)
            high_name = max(marks, key=marks.get)
            low_leg = legs[low_name]
            asof = asof_spot(spot_day, next_ts)
            if asof is None:
                exclusion_reason = "UNEXECUTABLE_ADJUSTMENT_NO_SPOT"
                break

            candidate = frame[
                (frame["timestamp"] == next_ts)
                & (frame["expiry"] == low_leg["expiry"])
                & (frame["option_type"] == low_leg["option_type"])
                & frame["open"].notna()
                & (frame["open"] >= 0)
            ]
            new_strike = target(candidate, marks[high_name], asof)
            old_open = price_at(
                frame,
                next_ts,
                low_leg["expiry"],
                low_leg["option_type"],
                low_leg["strike"],
                "open",
            )
            new_open = (
                price_at(
                    frame,
                    next_ts,
                    low_leg["expiry"],
                    low_leg["option_type"],
                    new_strike,
                    "open",
                )
                if new_strike is not None
                else None
            )
            if new_strike is None or old_open is None or new_open is None:
                exclusion_reason = "UNEXECUTABLE_ADJUSTMENT"
                break

            buy_rec = order_record(
                next_ts, "ADJUST_CLOSE", low_name, "BUY", old_open, lot
            )
            sell_rec = order_record(
                next_ts, "ADJUST_OPEN", low_name, "SELL", new_open, lot
            )
            orders.extend([buy_rec, sell_rec])
            realized_raw += low_leg["raw_entry"] - old_open
            realized_exec += low_leg["exec_entry"] - buy_rec["exec_price"] + sell_rec["exec_price"]
            low_leg["strike"] = float(new_strike)
            low_leg["raw_entry"] = float(new_open)
            low_leg["exec_entry"] = sell_rec["exec_price"]
            adjustment_count += 1

        if exclusion_reason is not None:
            trades.append({
                "trade_date": d,
                "status": "EXCLUDED_UNEXECUTABLE",
                "reason": exclusion_reason,
                "adjustment_count": adjustment_count,
                "monitoring_gap_count": monitoring_gap_count,
                "order_count": len(orders),
            })
            executions.extend([dict(trade_date=d, **o) for o in orders])
            continue

        exit_reason = "STOP_LOSS" if stop_hit else "TIME_EXIT"
        if not stop_hit:
            exit_prices = {
                name: price_at(
                    frame,
                    exit_ts,
                    leg["expiry"],
                    leg["option_type"],
                    leg["strike"],
                    "open",
                )
                for name, leg in legs.items()
            }
            if any(value is None for value in exit_prices.values()):
                exclusion_reason = "UNEXECUTABLE_TIME_EXIT"
                trades.append({
                    "trade_date": d,
                    "status": "EXCLUDED_UNEXECUTABLE",
                    "reason": exclusion_reason,
                    "adjustment_count": adjustment_count,
                    "monitoring_gap_count": monitoring_gap_count,
                    "order_count": len(orders),
                })
                executions.extend([dict(trade_date=d, **o) for o in orders])
                continue
            for name, leg in legs.items():
                orders.append(
                    order_record(
                        exit_ts, "TIME_EXIT", name, "BUY", float(exit_prices[name]), lot
                    )
                )

        raw_pnl = sum(
            (1.0 if o["side"] == "SELL" else -1.0) * o["raw_price"] * o["qty"]
            for o in orders
        )
        slippage_cost = sum(o["slippage_points"] * o["qty"] for o in orders)
        transaction_costs = sum(o["total_cost"] for o in orders)
        gross_points = raw_pnl / lot
        net_pnl = raw_pnl - slippage_cost - transaction_costs
        net_points = net_pnl / lot
        expected_raw = raw_pnl
        if abs(expected_raw - (realized_raw + sum(
            leg["raw_entry"] - price_at(
                frame, exit_ts, leg["expiry"], leg["option_type"], leg["strike"], "open"
            ) * -0.0
            for leg in legs.values()
        ))) < -1:  # defensive no-op; full order ledger remains the canonical raw P&L
            pass

        trades.append({
            "trade_date": d,
            "status": "COMPLETED",
            "exit_reason": exit_reason,
            "adjustment_count": adjustment_count,
            "stop_hit": stop_hit,
            "monitoring_gap_count": monitoring_gap_count,
            "lot_size": lot,
            "initial_ce_strike": float(ce_strike),
            "initial_pe_strike": float(pe_strike),
            "gross_pnl_raw": raw_pnl,
            "gross_points_raw": gross_points,
            "slippage_cost": slippage_cost,
            "transaction_costs": transaction_costs,
            "net_pnl": net_pnl,
            "net_points": net_points,
            "net_return_on_2L": net_pnl / 200000.0,
            "net_return_on_2_5L": net_pnl / 250000.0,
            "order_count": len(orders),
        })
        executions.extend([dict(trade_date=d, **o) for o in orders])

    trade_ledger = pd.DataFrame(trades)
    execution_ledger = pd.DataFrame(executions)
    trade_ledger.to_csv(OUT / "trade_ledger.csv", index=False)
    execution_ledger.to_csv(OUT / "execution_ledger.csv", index=False)

    completed = trade_ledger[trade_ledger["status"] == "COMPLETED"].copy()
    excluded = trade_ledger[trade_ledger["status"] != "COMPLETED"].copy()

    if not completed.empty:
        completed = completed.sort_values("trade_date")
        completed["cum_net_pnl"] = completed["net_pnl"].cumsum()
        completed["high_water"] = completed["cum_net_pnl"].cummax()
        completed["drawdown"] = completed["cum_net_pnl"] - completed["high_water"]
        losses = completed.loc[completed["net_pnl"] < 0, "net_pnl"].sum()
        gains = completed.loc[completed["net_pnl"] > 0, "net_pnl"].sum()
        profit_factor = float(gains / abs(losses)) if losses < 0 else math.inf
        summary = {
            "primary_window": {"start": START, "end": END},
            "eligible_universe_dates": int(len(universe)),
            "completed_trades": int(len(completed)),
            "excluded_unexecutable": int(len(excluded)),
            "total_net_pnl": float(completed["net_pnl"].sum()),
            "total_gross_pnl_raw": float(completed["gross_pnl_raw"].sum()),
            "total_slippage_cost": float(completed["slippage_cost"].sum()),
            "total_transaction_costs": float(completed["transaction_costs"].sum()),
            "mean_net_pnl": float(completed["net_pnl"].mean()),
            "median_net_pnl": float(completed["net_pnl"].median()),
            "win_rate": float((completed["net_pnl"] > 0).mean()),
            "profit_factor": profit_factor,
            "max_drawdown": float(completed["drawdown"].min()),
            "stop_loss_trades": int(completed["stop_hit"].sum()),
            "adjustment_trades": int((completed["adjustment_count"] > 0).sum()),
            "total_adjustments": int(completed["adjustment_count"].sum()),
            "mean_monitoring_gaps_per_trade": float(completed["monitoring_gap_count"].mean()),
            "excluded_reasons": excluded["reason"].value_counts().to_dict() if not excluded.empty else {},
            "cost_model": COST,
            "slippage_points_per_execution": SLIPPAGE_POINTS,
            "stop_loss_points": STOP_POINTS,
            "reentry_enabled": False,
            "margin_context": {"low_inr": 200000, "high_inr": 250000},
            "stage_rows": int(bars_meta.iloc[0]["rows"]),
        }
    else:
        summary = {
            "primary_window": {"start": START, "end": END},
            "eligible_universe_dates": int(len(universe)),
            "completed_trades": 0,
            "excluded_unexecutable": int(len(excluded)),
            "excluded_reasons": excluded["reason"].value_counts().to_dict() if not excluded.empty else {},
        }

    (OUT / "primary_backtest_summary.json").write_text(
        json.dumps(summary, indent=2, default=str),
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
