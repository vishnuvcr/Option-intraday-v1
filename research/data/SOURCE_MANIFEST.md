# Data Source Manifest

## Primary option data

**Source:** Hugging Face dataset "rissin/nse-options-intraday"  
**Pinned dataset revision:** 78b1c5468255d18cf492984bfe6fe4e3ac874d7c  
**Use:** 1-minute NIFTY option OHLC/volume history.

The pinned snapshot is used as a **composite source** because its Upstox track contains NIFTY 2024 and 2025 partitions, while its 2026 NIFTY partition is under the dataset's Kotak live track. This was discovered during automated acquisition and is recorded as a source-coverage finding, not silently substituted.

| Sample period | Dataset path | Source track |
|---|---|---|
| 2024 | upstox_intraday/NIFTY/NIFTY_2024.parquet | Upstox historical API |
| 2025 | upstox_intraday/NIFTY/NIFTY_2025.parquet | Upstox historical API |
| 2026 | kotak_live/NIFTY/NIFTY_2026.parquet | Kotak live collection |

Dataset card: https://huggingface.co/datasets/rissin/nse-options-intraday  
Pinned revision: https://huggingface.co/datasets/rissin/nse-options-intraday/commit/78b1c5468255d18cf492984bfe6fe4e3ac874d7c

The workflow records SHA-256 hashes, byte sizes, source path, revision and download time for every partition.

## Primary spot data

**Source:** GitHub release voletiramu/nse-fno-1min-data, tag indices-v1.0.0, asset nifty_indices_5yr.zip.  
**Spot file:** NIFTY_5min_5yr_2021_2026.csv  
**Coverage:** April 2021–April 2026.  
**Provider stated in release:** Zerodha Kite, NIFTY 50 spot index.  
**Release asset SHA-256:** 0c1f3de848a4e8c05e233c195685e7ae560d56d08df8baba8b2ffcfac699d3f8.

## Common primary window

The primary backtest window is limited to the overlap of option and spot history: **2024-10-01 through 2026-04-30**, subject to day-level completeness and contract checks.

## Source hierarchy and fallback

1. NSE/exchange data where directly accessible.
2. Public reproducible datasets with explicit provenance.
3. Public GitHub/Kaggle/Hugging Face sources with explicit provenance.
4. Composite datasets only when a documented source coverage gap requires it.

A source failure or coverage gap is logged before fallback is used.

## Reproducibility

Large raw files remain in the GitHub Actions cache. The repository stores deterministic acquisition/validation code, source manifests, hashes, and research results.
