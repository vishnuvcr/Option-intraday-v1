from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import duckdb
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MANIFEST = ROOT / "research" / "data" / "ACQUISITION_MANIFEST.json"
EXCLUSIONS = ROOT / "research" / "data" / "DATA_EXCLUSIONS.md"
UNIVERSE_OUT = ROOT / "research" / "data" / "CONTRACT_UNIVERSE.csv"
SUMMARY_OUT = ROOT / "research" / "data" / "CONTRACT_VALIDATION_SUMMARY.json"

START = "2024-10-01"
END = "2025-12-31"
ENTRY_TIME = "09:30:00"
SESSION_START = "09:30:00"
SESSION_END = "15:15:00"
EXPECTED_MINUTES = 346
NEAR_ATM_MAX_DISTANCE = 25.0  # NSE NIFTY weekly strike interval is 50 points


def lot_size(expiry: pd.Timestamp) -> int:
    d = expiry.date()
    # NSE Circular 131/2024: NIFTY weekly expiry 19-Dec-2024 was the last
    # weekly expiry with the old 25 lot; 02-Jan-2025 was the first revised
    # weekly expiry. The 26-Dec-2024 weekly expiry remained on the old regime.
    if d <= pd.Timestamp("2024-12-26").date():
        return 25
    # NSE Circular 176/2025: weekly/monthly contracts retain 75 through
    # 30-Dec-2025 expiry; subsequent contracts use 65.
    if d <= pd.Timestamp("2025-12-30").date():
        return 75
    return 65


def sql_file_list(paths: list[Path]) -> str:
    quoted = []
    for p in paths:
        quoted.append("'" + str(p).replace("'", "''") + "'")
    return "[" + ", ".join(quoted) + "]"


def main() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    option_paths = [CACHE / "hf_options" / item["source_path"] for item in manifest["options_source"]["files"]]

    spot_path = ROOT / "data" / "cache" / "spot" / "extracted" / "NIFTY_5min_5yr_2021_2026.csv"
    if not spot_path.exists():
        raise FileNotFoundError(f"Spot file missing: {spot_path}")

    con = duckdb.connect()
    con.execute("SET TimeZone='Asia/Kolkata'")
    con.execute("PRAGMA threads=4")
    con.execute("PRAGMA enable_progress_bar=false")
    con.execute("SET TimeZone='Asia/Kolkata'")
    files_sql = sql_file_list(option_paths)
    con.execute(
        f"CREATE OR REPLACE VIEW options AS "
        f"SELECT * FROM read_parquet({files_sql}, union_by_name=true)"
    )

    spot = pd.read_csv(spot_path)
    spot["timestamp"] = pd.to_datetime(spot["timestamp"], errors="coerce")
    spot = spot.dropna(subset=["timestamp"])
    spot["trade_date"] = spot["timestamp"].dt.date.astype(str)
    spot_0930 = spot[
        (spot["timestamp"].dt.strftime("%H:%M:%S") == ENTRY_TIME)
        & (spot["timestamp"].dt.strftime("%Y-%m-%d") >= START)
        & (spot["timestamp"].dt.strftime("%Y-%m-%d") <= END)
    ][["trade_date", "close"]].rename(columns={"close": "spot_0930"})
    con.register("spot_0930", spot_0930)

    # Map each trade date to the two nearest listed expiries on/after that date.
    expiry_sql = """
    WITH pairs AS (
        SELECT DISTINCT
            CAST(date AS DATE) AS trade_date,
            CAST(expiry AS DATE) AS expiry
        FROM options
        WHERE CAST(date AS DATE) BETWEEN DATE '2024-10-01' AND DATE '2025-12-31'
    ),
    ranked AS (
        SELECT
            trade_date,
            expiry,
            ROW_NUMBER() OVER (
                PARTITION BY trade_date
                ORDER BY expiry
            ) AS rn
        FROM pairs
        WHERE expiry >= trade_date
    )
    SELECT
        trade_date,
        MAX(CASE WHEN rn = 1 THEN expiry END) AS current_expiry,
        MAX(CASE WHEN rn = 2 THEN expiry END) AS next_expiry
    FROM ranked
    GROUP BY trade_date
    ORDER BY trade_date
    """
    expiry_map = con.execute(expiry_sql).df()
    expiry_map["trade_date"] = pd.to_datetime(expiry_map["trade_date"]).dt.strftime("%Y-%m-%d")
    expiry_map["current_expiry"] = pd.to_datetime(expiry_map["current_expiry"], errors="coerce")
    expiry_map["next_expiry"] = pd.to_datetime(expiry_map["next_expiry"], errors="coerce")

    con.register("expiry_map_df", expiry_map)

    # Select the nearest available strike separately for the current-week CE
    # and next-week PE using only 09:30 data and the 09:30 spot observation.
    entry_sql = """
    WITH chain AS (
        SELECT
            CAST(o.date AS DATE) AS trade_date,
            CAST(o.expiry AS DATE) AS expiry,
            o.option_type,
            CAST(o.strike AS DOUBLE) AS strike,
            CAST(o.open AS DOUBLE) AS entry_open,
            s.spot_0930,
            CASE
                WHEN CAST(o.expiry AS DATE) = m.current_expiry AND o.option_type = 'CE'
                    THEN 'current_ce'
                WHEN CAST(o.expiry AS DATE) = m.next_expiry AND o.option_type = 'PE'
                    THEN 'next_pe'
                ELSE NULL
            END AS leg
        FROM options o
        JOIN expiry_map_df m
          ON CAST(o.date AS DATE) = CAST(m.trade_date AS DATE)
        JOIN spot_0930 s
          ON CAST(o.date AS DATE) = CAST(s.trade_date AS DATE)
        WHERE CAST(o.date AS DATE) BETWEEN DATE '2024-10-01' AND DATE '2025-12-31'
          AND CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS TIME) = TIME '09:30:00'
          AND (
              (CAST(o.expiry AS DATE) = m.current_expiry AND o.option_type = 'CE')
              OR
              (CAST(o.expiry AS DATE) = m.next_expiry AND o.option_type = 'PE')
          )
    ),
    ranked AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY trade_date, leg
                   ORDER BY ABS(strike - spot_0930), strike
               ) AS rn
        FROM chain
        WHERE leg IS NOT NULL
    )
    SELECT
        trade_date,
        leg,
        expiry,
        strike,
        entry_open,
        spot_0930
    FROM ranked
    WHERE rn = 1
    ORDER BY trade_date, leg
    """
    entries = con.execute(entry_sql).df()
    entries["trade_date"] = pd.to_datetime(entries["trade_date"]).dt.strftime("%Y-%m-%d")
    entries["expiry"] = pd.to_datetime(entries["expiry"], errors="coerce")

    # Exclude source dates that have no 09:30 spot.
    all_dates = set(expiry_map["trade_date"].dropna().astype(str))
    spot_0930_dates = set(spot_0930["trade_date"].astype(str))
    dates_without_0930 = sorted(all_dates - spot_0930_dates)

    reasons: dict[str, list[str]] = {d: [] for d in sorted(all_dates)}
    for d in dates_without_0930:
        reasons.setdefault(d, []).append("missing_09:30_spot")

    # Pivot initial legs and validate the two expiry/strike contracts.
    ce = entries[entries["leg"] == "current_ce"].copy()
    pe = entries[entries["leg"] == "next_pe"].copy()

    ce = ce.rename(columns={
        "expiry": "current_expiry",
        "strike": "current_ce_strike",
        "entry_open": "current_ce_entry_open",
        "spot_0930": "spot_0930_ce",
    })
    pe = pe.rename(columns={
        "expiry": "next_expiry",
        "strike": "next_pe_strike",
        "entry_open": "next_pe_entry_open",
        "spot_0930": "spot_0930_pe",
    })

    universe = expiry_map.merge(
        ce[[
            "trade_date", "current_expiry", "current_ce_strike",
            "current_ce_entry_open", "spot_0930_ce"
        ]],
        on=["trade_date", "current_expiry"],
        how="left",
    ).merge(
        pe[[
            "trade_date", "next_expiry", "next_pe_strike",
            "next_pe_entry_open", "spot_0930_pe"
        ]],
        on=["trade_date", "next_expiry"],
        how="left",
    )

    universe["spot_0930"] = universe["spot_0930_ce"].fillna(universe["spot_0930_pe"])
    universe["lot_size_current"] = universe["current_expiry"].apply(
        lambda x: lot_size(x) if pd.notna(x) else math.nan
    )
    universe["lot_size_next"] = universe["next_expiry"].apply(
        lambda x: lot_size(x) if pd.notna(x) else math.nan
    )
    universe["lot_size"] = universe["lot_size_current"]

    for i, row in universe.iterrows():
        d = str(row["trade_date"])
        if d in reasons and reasons[d]:
            continue
        if pd.isna(row["current_expiry"]) or pd.isna(row["next_expiry"]):
            reasons[d].append("missing_two_weekly_expiries")
            continue
        if int(row["lot_size_current"]) != int(row["lot_size_next"]):
            reasons[d].append(
                f"lot_size_mismatch:{int(row['lot_size_current'])}_vs_{int(row['lot_size_next'])}"
            )
            continue
        if pd.isna(row["current_ce_strike"]) or pd.isna(row["next_pe_strike"]):
            reasons[d].append("missing_09:30_entry_strike")
            continue
        ce_distance = abs(float(row["current_ce_strike"]) - float(row["spot_0930"]))
        pe_distance = abs(float(row["next_pe_strike"]) - float(row["spot_0930"]))
        if ce_distance > NEAR_ATM_MAX_DISTANCE or pe_distance > NEAR_ATM_MAX_DISTANCE:
            reasons[d].append(
                f"near_atm_data_gap:ce_{ce_distance:.2f}_pe_{pe_distance:.2f}_max_{NEAR_ATM_MAX_DISTANCE:.2f}"
            )
            continue
        if float(row["current_ce_entry_open"]) <= 0 or float(row["next_pe_entry_open"]) <= 0:
            reasons[d].append("nonpositive_09:30_entry_price")
            continue

    # Contract-level completeness for the two initial legs from 09:30 through 15:15.
    eligible = universe[
        ~universe["trade_date"].astype(str).isin(dates_without_0930)
        & universe["current_ce_strike"].notna()
        & universe["next_pe_strike"].notna()
    ].copy()

    con.register("eligible_universe", eligible[[
        "trade_date", "current_expiry", "current_ce_strike", "next_expiry", "next_pe_strike"
    ]])

    completeness_sql = """
    WITH active_contracts AS (
        SELECT trade_date, current_expiry AS expiry, current_ce_strike AS strike, 'CE' AS option_type
        FROM eligible_universe
        UNION ALL
        SELECT trade_date, next_expiry AS expiry, next_pe_strike AS strike, 'PE' AS option_type
        FROM eligible_universe
    )
    SELECT
        a.trade_date,
        a.expiry,
        a.strike,
        a.option_type,
        COUNT(DISTINCT o.timestamp) AS distinct_minutes,
        MIN(o.timestamp) AS first_timestamp,
        MAX(o.timestamp) AS last_timestamp,
        COUNT(*) AS row_count
    FROM active_contracts a
    LEFT JOIN options o
      ON CAST(o.date AS DATE) = CAST(a.trade_date AS DATE)
     AND CAST(o.expiry AS DATE) = CAST(a.expiry AS DATE)
     AND CAST(o.strike AS DOUBLE) = CAST(a.strike AS DOUBLE)
     AND o.option_type = a.option_type
     AND CAST(o.timestamp AS DATE) = CAST(a.trade_date AS DATE)
     AND CAST(o.timestamp AT TIME ZONE 'Asia/Kolkata' AS TIME) BETWEEN TIME '09:30:00' AND TIME '15:15:00'
    GROUP BY a.trade_date, a.expiry, a.strike, a.option_type
    """
    completeness = con.execute(completeness_sql).df()

    # Do not silently forward-fill missing option bars. Phase 3 records
    # completeness; the Phase 4 engine will exclude a trade if a required
    # execution/monitoring observation is unavailable. For PIT validation,
    # an initial contract needs at least its 09:30 entry and a 15:15 exit
    # observation to be eligible for the primary ledger.
    bad_days = set()
    completeness["distinct_minutes"] = completeness["distinct_minutes"].fillna(0).astype(int)
    completeness["has_minimum_execution_observations"] = completeness["distinct_minutes"] >= 2
    for _, row in completeness.iterrows():
        if not bool(row["has_minimum_execution_observations"]):
            bad_days.add(str(row["trade_date"]))
            reasons.setdefault(str(row["trade_date"]), []).append(
                f"missing_entry_or_exit_observation:{row['option_type']}:{int(row['distinct_minutes'])}_minutes"
            )

    # Global duplicate-key audit over the validated primary source.
    duplicate_sql = """
    SELECT
        COUNT(*) AS duplicate_key_groups,
        COALESCE(SUM(cnt - 1), 0) AS duplicate_rows
    FROM (
        SELECT
            timestamp,
            expiry,
            strike,
            option_type,
            COUNT(*) AS cnt
        FROM options
        WHERE CAST(date AS DATE) BETWEEN DATE '2024-10-01' AND DATE '2025-12-31'
        GROUP BY timestamp, expiry, strike, option_type
        HAVING COUNT(*) > 1
    ) x
    """
    duplicates = con.execute(duplicate_sql).df().iloc[0].to_dict()

    universe["eligible"] = universe["trade_date"].astype(str).map(
        lambda d: len(reasons.get(d, [])) == 0 and d not in bad_days
    )
    universe["exclusion_reason"] = universe["trade_date"].astype(str).map(
        lambda d: ";".join(reasons.get(d, []))
    )
    universe["lot_size_rule"] = universe["current_expiry"].map(
        lambda x: f"through_2024-12-26:25;2025-01-02_through_2025-12-30:75;after_2025-12-30:65" if pd.notna(x) else ""
    )

    UNIVERSE_OUT.parent.mkdir(parents=True, exist_ok=True)
    universe.to_csv(UNIVERSE_OUT, index=False)

    summary = {
        "primary_window": {"start": START, "end": END},
        "trade_dates_in_option_source": int(len(expiry_map)),
        "trade_dates_with_09_30_spot": int(len(spot_0930_dates)),
        "trade_dates_missing_09_30_spot": dates_without_0930,
        "trade_dates_excluded_for_initial_contract_quality": sorted(
            [d for d, r in reasons.items() if r and d not in dates_without_0930]
        ),
        "eligible_trade_dates": int(universe["eligible"].sum()),
        "current_expiry_unique_count": int(universe["current_expiry"].nunique()),
        "next_expiry_unique_count": int(universe["next_expiry"].nunique()),
        "duplicate_key_groups": int(duplicates["duplicate_key_groups"]),
        "duplicate_rows": int(duplicates["duplicate_rows"]),
        "expected_minutes_0930_to_1515": EXPECTED_MINUTES,
        "completeness_policy": "record gaps in Phase 3; require minimum entry/exit observations; Phase 4 excludes unexecutable monitoring events without forward-fill",
        "lot_size_regimes": {
            "through_2024-12-26": 25,
            "2025-01-02_through_2025-12-30": 75,
            "after_2025-12-30": 65,
        },
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")

    print(json.dumps(summary, indent=2, default=str))

    if int(duplicates["duplicate_key_groups"]) != 0:
        sys.exit("Contract validation failed: duplicate option keys found")

    if int(universe["eligible"].sum()) < 100:
        sys.exit("Contract validation failed: fewer than 100 eligible trade dates")

if __name__ == "__main__":
    main()
