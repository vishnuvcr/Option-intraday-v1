# Data Source Manifest

## Primary option data

**Source:** Hugging Face dataset "rissin/nse-options-intraday"
**Track:** upstox_intraday/NIFTY
**Granularity:** 1 minute
**Pinned dataset revision:** 78b1c5468255d18cf492984bfe6fe4e3ac874d7c
**Coverage:** October 2024 onward for the intraday track at the time of the pinned snapshot.
**Schema:** date, timestamp, underlying, expiry, strike, option_type, exercise_style, OHLC, volume, OI, settle_price, source, granularity.
**Use:** option premium history, expiry/strike universe.

Dataset card: https://huggingface.co/datasets/rissin/nse-options-intraday
Pinned revision: https://huggingface.co/datasets/rissin/nse-options-intraday/commit/78b1c5468255d18cf492984bfe6fe4e3ac874d7c

The acquisition workflow downloads only the NIFTY yearly Parquet partitions needed for the reproducible common sample and records SHA-256 hashes after download.

## Primary spot data

**Source:** GitHub release voletiramu/nse-fno-1min-data, tag indices-v1.0.0, asset nifty_indices_5yr.zip.
**Spot file:** NIFTY_5min_5yr_2021_2026.csv
**Coverage:** April 2021–April 2026.
**Provider stated in release:** Zerodha Kite, NIFTY 50 spot index.
**Release asset SHA-256:** 0c1f3de848a4e8c05e233c195685e7ae560d56d08df8baba8b2ffcfac699d3f8.

## Common primary window

The primary backtest window is limited to the overlap of option and spot history: 2024-10-01 through 2026-04-30, subject to day-level completeness checks.

## Source hierarchy and fallback

1. NSE/exchange data where directly accessible.
2. Public reproducible datasets with explicit provenance.
3. Public GitHub/Kaggle/Hugging Face sources with explicit provenance.
4. Composite sources only when a documented source coverage gap requires it.

A source failure is logged before fallback is used.

## Reproducibility

The workflow records source URLs, immutable revisions/tags, file hashes, download timestamp, row counts, date ranges, and validation outcomes. Large raw files are kept in GitHub Actions cache; the repository stores code, manifests, hashes and research results.
