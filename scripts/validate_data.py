from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import polars as pl
import pyarrow.parquet as pq

# Polars currently rejects the fixed-offset timezone metadata (+05:30) stored by
# some Parquet writers. Keep the source timezone for audit via PyArrow, while
# treating the timestamp as a string for chronology checks.
os.environ.setdefault("POLARS_IGNORE_TIMEZONE_PARSE_ERROR", "1")

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MANIFEST = CACHE / "acquisition_manifest.json"
REPORT_PATH = CACHE / "validation_report.json"
COMMON_START = pd.Timestamp("2024-10-01")
COMMON_END = pd.Timestamp("2026-04-30 23:59:59")

EXPECTED_OPTION_COLUMNS = {
    "date", "timestamp", "underlying", "expiry", "strike", "option_type",
    "open", "high", "low", "close", "volume", "oi", "settle_price",
    "source", "granularity",
}

def validate_options(path: Path) -> dict:
    arrow_schema = pq.ParquetFile(path).schema_arrow
    cols = set(arrow_schema.names)
    missing = sorted(EXPECTED_OPTION_COLUMNS - cols)
    if missing:
        raise AssertionError(f"{path}: missing columns {missing}")

    ts_arrow = arrow_schema.field("timestamp").type
    ts_metadata = str(ts_arrow)

    lf = pl.scan_parquet(path)
    ts_str = pl.col("timestamp").cast(pl.String)
    trade_date = pl.col("date").cast(pl.String).str.slice(0, 10)
    expiry_date = pl.col("expiry").cast(pl.String).str.slice(0, 10)
    ts_date = ts_str.str.slice(0, 10)
    ts_hour = ts_str.str.slice(11, 2).cast(pl.Int16, strict=False)
    ts_minute = ts_str.str.slice(14, 2).cast(pl.Int16, strict=False)
    ts_second = ts_str.str.slice(17, 2).cast(pl.Int16, strict=False)

    metrics = lf.select([
        pl.len().alias("rows"),
        pl.col("date").cast(pl.String).str.slice(0, 10).str.strptime(pl.Date, strict=False).min().alias("min_date"),
        pl.col("date").cast(pl.String).str.slice(0, 10).str.strptime(pl.Date, strict=False).max().alias("max_date"),
        ts_str.min().alias("min_timestamp"),
        ts_str.max().alias("max_timestamp"),
        (pl.col("underlying") != "NIFTY").fill_null(True).sum().alias("bad_underlying_rows"),
        (~pl.col("option_type").is_in(["CE", "PE"])).fill_null(True).sum().alias("bad_option_type_rows"),
        (pl.col("granularity") != "1min").fill_null(True).sum().alias("bad_granularity_rows"),
        (pl.col("strike") <= 0).fill_null(True).sum().alias("bad_strike_rows"),
        (pl.col("open") < 0).fill_null(True).sum().alias("bad_open_rows"),
        (pl.col("high") < 0).fill_null(True).sum().alias("bad_high_rows"),
        (pl.col("low") < 0).fill_null(True).sum().alias("bad_low_rows"),
        (pl.col("close") < 0).fill_null(True).sum().alias("bad_close_rows"),
        (pl.col("high") < pl.max_horizontal("open", "close", "low")).fill_null(True).sum().alias("bad_high_relation_rows"),
        (pl.col("low") > pl.min_horizontal("open", "close", "high")).fill_null(True).sum().alias("bad_low_relation_rows"),
        trade_date.str.strptime(pl.Date, strict=False).is_null().sum().alias("unparseable_trade_date_rows"),
        expiry_date.str.strptime(pl.Date, strict=False).is_null().sum().alias("unparseable_expiry_rows"),
        (
            (expiry_date.str.strptime(pl.Date, strict=False) < trade_date.str.strptime(pl.Date, strict=False))
            .fill_null(True)
        ).sum().alias("expiry_before_trade_rows"),
        (ts_date != trade_date).fill_null(True).sum().alias("timestamp_date_mismatch_rows"),
        (ts_second != 0).fill_null(True).sum().alias("non_minute_boundary_rows"),
        (
            (ts_hour * 60 + ts_minute < 555)
            | (ts_hour * 60 + ts_minute > 930)
        ).fill_null(True).sum().alias("outside_session_rows"),
        ts_date.n_unique().alias("distinct_timestamp_dates"),
        trade_date.n_unique().alias("distinct_trade_dates"),
        expiry_date.n_unique().alias("distinct_expiries"),
        pl.col("strike").n_unique().alias("distinct_strikes"),
    ]).collect().to_dicts()[0]

    duplicate_key_groups = (
        lf.group_by(["timestamp", "expiry", "strike", "option_type"])
        .len()
        .filter(pl.col("len") > 1)
        .select(pl.len())
        .collect()
        .item()
    )
    null_close = lf.filter(pl.col("close").is_null()).select(pl.len()).collect().item()

    return {
        "path": str(path.relative_to(ROOT)),
        "timestamp_parquet_type": ts_metadata,
        **{k: (int(v) if isinstance(v, (int, float)) else v) for k, v in metrics.items()},
        "duplicate_key_groups": int(duplicate_key_groups),
        "null_close_rows": int(null_close),
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
    exact_0930 = common[(common["_ts"].dt.hour == 9) & (common["_ts"].dt.minute == 30)]

    return {
        "rows": int(len(df)),
        "min_timestamp": str(ts.min()),
        "max_timestamp": str(ts.max()),
        "timestamp_timezone_metadata": str(getattr(ts.dt, "tz", None)),
        "duplicate_timestamps": int(df["timestamp"].duplicated().sum()),
        "bad_ohlc_rows": int(
            ((df["high"] < df[["open", "close", "low"]].max(axis=1))
             | (df["low"] > df[["open", "close", "high"]].min(axis=1))
             | (df[["open", "high", "low", "close"]] < 0).any(axis=1)).sum()
        ),
        "common_window_rows": int(len(common)),
        "common_window_0930_rows": int(len(exact_0930)),
        "common_window_distinct_dates": int(common["_ts"].dt.date.nunique()),
        "median_seconds_between_spot_bars": float(common["_ts"].sort_values().diff().dt.total_seconds().median()) if len(common) > 1 else None,
        "common_window_complete_for_0930": bool(len(exact_0930) > 0),
    }

def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError("Run scripts/acquire_data.py before validate_data.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))

    option_reports = [validate_options(ROOT / item["path"]) for item in manifest["options"]["files"]]
    spot_path = ROOT / manifest["spot"]["file"]
    spot_report = validate_spot(spot_path)

    option_dates: set = set()
    for item in manifest["options"]["files"]:
        p = ROOT / item["path"]
        dates = (
            pl.scan_parquet(p)
            .select(pl.col("date").cast(pl.String).str.slice(0, 10).unique())
            .collect()
            .to_series()
            .to_list()
        )
        option_dates.update(pd.Timestamp(x).date() for x in dates if x)

    spot_ts = pd.to_datetime(pd.read_csv(spot_path)["timestamp"], errors="coerce")
    spot_dates = set(spot_ts.dt.date)
    overlap = option_dates & spot_dates
    spot_report["distinct_option_spot_dates"] = int(len(overlap))
    spot_report["primary_window_overlap_dates"] = int(
        len(overlap & set(pd.date_range(COMMON_START, COMMON_END, freq="D").date))
    )

    report = {"options": option_reports, "spot": spot_report}
    REPORT_PATH.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))

    failures = []
    checks = [
        "bad_underlying_rows", "bad_option_type_rows", "bad_granularity_rows",
        "bad_strike_rows", "bad_open_rows", "bad_high_rows", "bad_low_rows",
        "bad_close_rows", "bad_high_relation_rows", "bad_low_relation_rows",
        "unparseable_trade_date_rows", "unparseable_expiry_rows",
        "expiry_before_trade_rows", "timestamp_date_mismatch_rows",
        "non_minute_boundary_rows", "outside_session_rows",
        "duplicate_key_groups", "null_close_rows",
    ]
    for r in option_reports:
        for key in checks:
            if int(r.get(key, 0)) != 0:
                failures.append(f"{r['path']}:{key}={r[key]}")

    if spot_report["bad_ohlc_rows"] or spot_report["duplicate_timestamps"]:
        failures.append("spot:bad_ohlc_or_duplicate_timestamps")
    if not spot_report["common_window_complete_for_0930"]:
        failures.append("spot:no_09_30_observation_in_common_window")
    if spot_report["primary_window_overlap_dates"] == 0:
        failures.append("spot/options:no_primary_window_date_overlap")

    if failures:
        sys.exit("Validation failed: " + "; ".join(failures))

if __name__ == "__main__":
    main()
