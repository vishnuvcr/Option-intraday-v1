# Data Source Manifest

## Primary option data

**Source:** Hugging Face dataset `rissin/nse-options-intraday`  
**Track:** `upstox_intraday/NIFTY`  
**Granularity:** 1 minute  
**Advertised coverage:** October 2024 onward  
**Schema:** date, timestamp, underlying, expiry, strike, option_type, OHLC, volume, OI, settle_price, source, granularity.  
**Use:** option premium history, expiry/strike universe.

The workflow downloads only the NIFTY yearly Parquet partitions needed for the reproducible common sample and records SHA-256 hashes after download.

## Primary spot data

**Source:** GitHub release `voletiramu/nse-fno-1min-data`, tag `indices-v1.0.0`, asset `nifty_indices_5yr.zip`.  
**Spot file:** `NIFTY_5min_5yr_2021_2026.csv`  
**Coverage:** April 2021–April 2026.  
**Provider stated in release:** Zerodha Kite, NIFTY 50 spot index.  
**Release asset SHA-256:** `0c1f3de848a4e8c05e233c195685e7ae560d56d08df8baba8b2ffcfac699d3f8`.

The common primary backtest window is therefore limited to the overlap of option and spot data: **2024-10-01 through 2026-04-30**, subject to day-level completeness checks.

## Source hierarchy and fallback

1. NSE/exchange data where directly accessible.
2. Public reproducible datasets with explicit provenance.
3. Composite sources when a single free source cannot cover both option and spot history.

A failure of one source must be logged before fallback is used.

## Data rights / reproducibility

The workflow records the exact source URLs, revision/commit/tag, file hashes, download timestamp, row counts, date ranges, and validation outcomes. Raw large files are kept in GitHub Actions cache/artifacts rather than committed to Git history; the repository stores manifests and deterministic code.
