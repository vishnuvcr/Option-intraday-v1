# Research Status

**Repository:** `vishnuvcr/Option-intraday-v1`  
**Research target:** Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put  
**Date:** 2026-10-05

## Current phase

**Phase 2 — Data acquisition & validation: final validator committed; rerun pending**

| Phase | Status |
|---|---|
| 0 Governance | ✅ passed |
| 1 Strategy freeze | ✅ tester passed |
| 2 Data acquisition | 🟡 workflow implemented/running |
| 3 Data validation | ⚪ pending |
| 4 Engine/cost model | ⚪ pending |
| 5 Primary backtest | ⚪ pending |
| 6 Robustness | ⚪ pending |
| 7 Independent tester | ⚪ pending |
| 8 OOS | ⚪ pending |
| 9 Manuscript | ⚪ pending |

## Immediate gate

P1 passed. Independent P2 audit blocked the data gate; developer remediated the listed reproducibility and validation defects. A source-coverage gap and validator/data-quality issues were remediated. The primary reproducible sample is frozen at 2024-10-01 through 2025-12-31. Minor 2024 out-of-session source contamination is explicitly reported and filtered. The corrected workflow must complete successfully and pass independent re-audit before Phase 3.

## Key known limitation

The user-provided rule says “re-entry if time and situation permits” but does not define a deterministic re-entry condition. The primary backtest will therefore not invent one. This is a specification limitation, not a model optimization.

## Data candidate

Public Hugging Face `rissin/nse-options-intraday` currently advertises NIFTY/BANKNIFTY/SENSEX 1-minute intraday coverage from October 2024 onward. Source provenance and license terms must be checked in Phase 2 before results are promoted.

## Cost candidate

Paytm Money's current public F&O FAQ states ₹10 brokerage per executed F&O order; statutory charges are separate and are applied from current official exchange/regulatory schedules with the historical schedule matched to each test date.
