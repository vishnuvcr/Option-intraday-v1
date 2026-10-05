from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MANIFEST = CACHE / "acquisition_manifest.json"
REPORT_PATH = CACHE / "validation_report.json"
COMMON_START = pd.Timestamp("2024-10-01")
COMMON_END = pd.Timestamp("2025-12-31 23:59:59")

EXPECTED_OPTION_COLUMNS = {
    "date", "timestamp", "underlying", "expiry", "strike", "option_type",
    "open", "high", "low", "close", "volume", "oi", "settle_price",
    "source", "granularity",
}

def validate_options(path: Path) -> dict:
    pf = pq.ParquetFile(path)
    schema = pf.schema_arrow
    cols = set(schema.names)
    missing = sorted(EXPECTED_OPTION_COLUMNS - cols)
    if missing:
        raise AssertionError(f"{path}: missing columns {missing}")

    totals = {
        "rows": 0,
        "bad_underlying_rows": 0,
        "bad_option_type_rows": 0,
        "bad_granularity_rows": 0,
        "bad_strike_rows": 0,
        "bad_open_rows": 0,
        "bad_high_rows": 0,
        "bad_low_rows": 0,
        "bad_close_rows": 0,
        "bad_high_relation_rows": 0,
        "bad_low_relation_rows": 0,
        "unparseable_trade_date_rows": 0,
        "unparseable_expiry_rows": 0,
        "expiry_before_trade_rows": 0,
        "timestamp_date_mismatch_rows": 0,
        "non_minute_boundary_rows": 0,
        "outside_session_rows": 0,
        "null_close_rows": 0,
        "intra_batch_duplicate_key_rows": 0,
    }

    min_date = None
    max_date = None
    min_ts = None
    max_ts = None
    timestamp_dtype = str(schema.field("timestamp").type)

    columns = [
        "date", "timestamp", "underlying", "expiry", "strike", "option_type",
        "open", "high", "low", "close", "granularity"
    ]

    for batch in pf.iter_batches(batch_size=250_000, columns=columns):
        df = batch.to_pandas()
        totals["rows"] += len(df)

        underlying = df["underlying"].astype("string")
        option_type = df["option_type"].astype("string")
        granularity = df["granularity"].astype("string")

        trade_date = pd.to_datetime(df["date"], errors="coerce")
        expiry_date = pd.to_datetime(df["expiry"], errors="coerce")
        timestamp = pd.to_datetime(df["timestamp"], errors="coerce")

        totals["bad_underlying_rows"] += int((underlying.fillna("") != "NIFTY").sum())
        totals["bad_option_type_rows"] += int((~option_type.isin(["CE", "PE"])).fillna(True).sum())
        totals["bad_granularity_rows"] += int((granularity.fillna("") != "1min").sum())
        strike = pd.to_numeric(df["strike"], errors="coerce")
        totals["bad_strike_rows"] += int((strike <= 0).fillna(True).sum())

        oo = pd.to_numeric(df["open"], errors="coerce")
        hh = pd.to_numeric(df["high"], errors="coerce")
        ll = pd.to_numeric(df["low"], errors="coerce")
        cc = pd.to_numeric(df["close"], errors="coerce")

        totals["bad_open_rows"] += int((oo < 0).fillna(True).sum())
        totals["bad_high_rows"] += int((hh < 0).fillna(True).sum())
        totals["bad_low_rows"] += int((ll < 0).fillna(True).sum())
        totals["bad_close_rows"] += int((cc < 0).fillna(True).sum())
        totals["null_close_rows"] += int(cc.isna().sum())

        extrema = pd.concat([oo, cc, ll], axis=1)
        totals["bad_high_relation_rows"] += int((hh < extrema.max(axis=1)).fillna(True).sum())
        extrema = pd.concat([oo, cc, hh], axis=1)
        totals["bad_low_relation_rows"] += int((ll > extrema.min(axis=1)).fillna(True).sum())

        totals["unparseable_trade_date_rows"] += int(trade_date.isna().sum())
        totals["unparseable_expiry_rows"] += int(expiry_date.isna().sum())
        comparable = trade_date.notna() & expiry_date.notna()
        totals["expiry_before_trade_rows"] += int((expiry_date[comparable] < trade_date[comparable]).sum())

        ts_valid = timestamp.notna()
        if ts_valid.any():
            totals["timestamp_date_mismatch_rows"] += int(
                (timestamp[ts_valid].dt.date != trade_date[ts_valid].dt.date).sum()
            )
            totals["non_minute_boundary_rows"] += int(
                ((timestamp[ts_valid].dt.second != 0) |
                 (timestamp[ts_valid].dt.microsecond != 0)).sum()
            )
            minute_of_day = timestamp[ts_valid].dt.hour * 60 + timestamp[ts_valid].dt.minute
            totals["outside_session_rows"] += int(
                ((minute_of_day < 555) | (minute_of_day > 930)).sum()
            )

        if len(df):
            bmin_date, bmax_date = trade_date.min(), trade_date.max()
            bmin_ts, bmax_ts = timestamp.min(), timestamp.max()
            min_date = bmin_date if min_date is None else min(min_date, bmin_date)
            max_date = bmax_date if max_date is None else max(max_date, bmax_date)
            min_ts = bmin_ts if min_ts is None else min(min_ts, bmin_ts)
            max_ts = bmax_ts if max_ts is None else max(max_ts, bmax_ts)

        key_dupes = df.duplicated(
            subset=["timestamp", "expiry", "strike", "option_type"], keep=False
        )
        totals["intra_batch_duplicate_key_rows"] += int(key_dupes.sum())

    if totals["rows"] == 0:
        raise AssertionError(f"{path}: zero rows")

    return {
        "path": str(path.relative_to(ROOT)),
        "timestamp_parquet_type": timestamp_dtype,
        "min_date": str(min_date),
        "max_date": str(max_date),
        "min_timestamp": str(min_ts),
        "max_timestamp": str(max_ts),
        **totals,
    }

def validate_spot(path: Path) -> dict:
    df = pd.read_csv(path)
    required = {"timestamp", "open", "high", "low", "close"}
    missing = sorted(required - set(df.columns))
    if missing:
        raise AssertionError(f"spot file missing columns: {missing}")

    ts = pd.to_datetime(df["timestamp"], errors="coerce")
    if ts.isna().any():
        raise AssertionError("spot timestamp parsing produced NaT")

    common = df.loc[(ts >= COMMON_START) & (ts <= COMMON_END)].copy()
    common["_ts"] = ts.loc[common.index]
    common_dates = set(common["_ts"].dt.date.tolist())
    exact_0930 = common[(common["_ts"].dt.hour == 9) & (common["_ts"].dt.minute == 30)]
    dates_0930 = set(exact_0930["_ts"].dt.date.tolist())
    missing_0930_dates = sorted(str(d) for d in (common_dates - dates_0930))

    return {
        "rows": int(len(df)),
        "min_timestamp": str(ts.min()),
        "max_timestamp": str(ts.max()),
        "duplicate_timestamps": int(df["timestamp"].duplicated().sum()),
        "bad_ohlc_rows": int(
            ((df["high"] < df[["open", "close", "low"]].max(axis=1))
             | (df["low"] > df[["open", "close", "high"]].min(axis=1))
             | (df[["open", "high", "low", "close"]] < 0).any(axis=1)).sum()
        ),
        "common_window_rows": int(len(common)),
        "common_window_0930_rows": int(len(exact_0930)),
        "common_window_distinct_dates": int(len(common_dates)),
        "dates_without_0930_observation": missing_0930_dates,
        "median_seconds_between_spot_bars": float(
            common["_ts"].sort_values().diff().dt.total_seconds().median()
        ) if len(common) > 1 else None,
    }

def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError("Run scripts/acquire_data.py before validate_data.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    option_reports = [
        validate_options(ROOT / item["path"])
        for item in manifest["options"]["files"]
    ]
    spot_path = ROOT / manifest["spot"]["file"]
    spot_report = validate_spot(spot_path)

    option_dates = set()
    for item in manifest["options"]["files"]:
        pf = pq.ParquetFile(ROOT / item["path"])
        for batch in pf.iter_batches(batch_size=250_000, columns=["date"]):
            vals = pd.to_datetime(batch.column(0).to_pandas(), errors="coerce")
            option_dates.update(vals.dropna().dt.date.tolist())

    spot_ts = pd.to_datetime(pd.read_csv(spot_path)["timestamp"], errors="coerce")
    spot_dates = set(spot_ts.dt.date)
    overlap = option_dates & spot_dates
    spot_report["distinct_option_spot_dates"] = int(len(overlap))
    spot_report["primary_window_overlap_dates"] = int(
        len(overlap & set(pd.date_range(COMMON_START, COMMON_END, freq="D").date))
    )

    total_rows = sum(int(r["rows"]) for r in option_reports)
    total_outside = sum(int(r["outside_session_rows"]) for r in option_reports)
    outside_ratio = total_outside / total_rows if total_rows else 1.0

    report = {
        "primary_window": {"start": str(COMMON_START), "end": str(COMMON_END)},
        "options": option_reports,
        "spot": spot_report,
        "option_outside_session_ratio": outside_ratio,
        "global_duplicate_key_check": (
            "Deferred to Phase 3 contract-level validation; Phase 2 checks "
            "within-batch duplicates and the backtest engine filters to session times."
        ),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))

    failures = []
    checks = [
        "bad_underlying_rows", "bad_option_type_rows", "bad_granularity_rows",
        "bad_strike_rows", "bad_open_rows", "bad_high_rows", "bad_low_rows",
        "bad_close_rows", "bad_high_relation_rows", "bad_low_relation_rows",
        "unparseable_trade_date_rows", "unparseable_expiry_rows",
        "expiry_before_trade_rows", "timestamp_date_mismatch_rows",
        "non_minute_boundary_rows", "null_close_rows",
    ]

    for r in option_reports:
        if r["rows"] < 100_000:
            failures.append(f"{r['path']}:too_few_rows={r['rows']}")
        for key in checks:
            if int(r.get(key, 0)) != 0:
                failures.append(f"{r['path']}:{key}={r[key]}")
        if int(r.get("intra_batch_duplicate_key_rows", 0)) != 0:
            failures.append(
                f"{r['path']}:intra_batch_duplicate_key_rows={r['intra_batch_duplicate_key_rows']}"
            )

    if outside_ratio > 0.01:
        failures.append(f"options:outside_session_ratio={outside_ratio:.6f}")
    if spot_report["bad_ohlc_rows"] or spot_report["duplicate_timestamps"]:
        failures.append("spot:bad_ohlc_or_duplicate_timestamps")
    if spot_report["primary_window_overlap_dates"] == 0:
        failures.append("spot/options:no_primary_window_date_overlap")

    if failures:
        sys.exit("Validation failed: " + "; ".join(failures))

if __name__ == "__main__":
    main()
