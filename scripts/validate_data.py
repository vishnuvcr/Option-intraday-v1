from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import polars as pl

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data" / "cache"
MANIFEST = CACHE / "acquisition_manifest.json"
REPORT_PATH = CACHE / "validation_report.json"

EXPECTED_OPTION_COLUMNS = {
    "date", "timestamp", "underlying", "expiry", "strike", "option_type",
    "open", "high", "low", "close", "volume", "oi", "settle_price",
    "source", "granularity",
}

def validate_options(path: Path) -> dict:
    lf = pl.scan_parquet(path)
    cols = set(lf.collect_schema().names())
    missing = sorted(EXPECTED_OPTION_COLUMNS - cols)
    if missing:
        raise AssertionError(f"{path}: missing columns {missing}")

    sample = lf.select([
        pl.col("date").min().alias("min_date"),
        pl.col("date").max().alias("max_date"),
        pl.len().alias("rows"),
        pl.col("timestamp").min().alias("min_ts"),
        pl.col("timestamp").max().alias("max_ts"),
    ]).collect().to_dicts()[0]

    bad_ohlc = (
        lf.filter(
            (pl.col("high") < pl.max_horizontal("open", "close", "low"))
            | (pl.col("low") > pl.min_horizontal("open", "close", "high"))
            | (pl.col("open") < 0)
            | (pl.col("high") < 0)
            | (pl.col("low") < 0)
            | (pl.col("close") < 0)
        ).select(pl.len()).collect().item()
    )
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
        "rows": int(sample["rows"]),
        "min_date": str(sample["min_date"]),
        "max_date": str(sample["max_date"]),
        "min_timestamp": str(sample["min_ts"]),
        "max_timestamp": str(sample["max_ts"]),
        "bad_ohlc_rows": int(bad_ohlc),
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
    }

def main() -> None:
    if not MANIFEST.exists():
        raise FileNotFoundError("Run scripts/acquire_data.py before validate_data.py")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    option_reports = [validate_options(ROOT / item["path"]) for item in manifest["options"]["files"]]
    spot_report = validate_spot(ROOT / manifest["spot"]["file"])
    report = {"options": option_reports, "spot": spot_report}
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    if any(r["bad_ohlc_rows"] for r in option_reports) or spot_report["bad_ohlc_rows"]:
        sys.exit("Validation failed: bad OHLC rows")
    if any(r["duplicate_key_groups"] for r in option_reports) or spot_report["duplicate_timestamps"]:
        sys.exit("Validation failed: duplicate keys/timestamps")
    if any(r["null_close_rows"] for r in option_reports):
        sys.exit("Validation failed: null option close rows")

if __name__ == "__main__":
    main()
