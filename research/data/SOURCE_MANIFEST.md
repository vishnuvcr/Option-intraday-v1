# Data Source Manifest

## Primary option data

**Source:** Hugging Face dataset "rissin/nse-options-intraday"  
**Pinned dataset revision:** 78b1c5468255d18cf492984bfe6fe4e3ac874d7c  
**Use:** 1-minute NIFTY option OHLC/volume history.

The pinned snapshot provides the validated primary sample through 2025. Its 2026 NIFTY Kotak partition exists but was only 9,344 bytes in the acquisition manifest and is not included in the primary sample because completeness has not been established.

| Sample period | Dataset path | Source track | Primary use |
|---|---|---|---|
| 2024 | upstox_intraday/NIFTY/NIFTY_2024.parquet | Upstox historical API | Yes |
| 2025 | upstox_intraday/NIFTY/NIFTY_2025.parquet | Upstox historical API | Yes |
| 2026 | kotak_live/NIFTY/NIFTY_2026.parquet | Kotak live collection | Excluded pending completeness |

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

The primary backtest window is **2024-10-01 through 2025-12-31**, subject to day-level completeness and contract checks.

## Source hierarchy and fallback

1. NSE/exchange data where directly accessible.
2. Public reproducible datasets with explicit provenance.
3. Public GitHub/Kaggle/Hugging Face sources with explicit provenance.
4. Composite datasets only when a documented source coverage gap requires it.

A source failure or coverage gap is logged before fallback is used. A public Google Drive dataset advertised as Oct-2024 to Mar-2026 was identified from a public GitHub project, but its folder cannot currently be fetched reliably by the automated environment; it is therefore not used in the primary automated run.

## Reproducibility

Large raw files remain in the GitHub Actions cache. The repository stores deterministic acquisition/validation code, source manifests, hashes, and research results.
