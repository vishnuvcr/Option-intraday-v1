# Research Status

**Repository:** `vishnuvcr/Option-intraday-v1`  
**Research target:** Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put  
**Date:** 2026-10-05

## Current phase

**Phase 2 — Data acquisition & validation: workflow running**

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

P1 passed. Phase 2 now acquires and hashes public option + spot sources, validates schemas/invariants, caches data, and publishes manifest/report artifacts. Performance engine remains blocked until data gates pass.

## Key known limitation

The user-provided rule says “re-entry if time and situation permits” but does not define a deterministic re-entry condition. The primary backtest will therefore not invent one. This is a specification limitation, not a model optimization.

## Data candidate

Public Hugging Face `rissin/nse-options-intraday` currently advertises NIFTY/BANKNIFTY/SENSEX 1-minute intraday coverage from October 2024 onward. Source provenance and license terms must be checked in Phase 2 before results are promoted.

## Cost candidate

Paytm Money's current public F&O FAQ states ₹10 brokerage per executed F&O order; statutory charges are separate and are applied from current official exchange/regulatory schedules with the historical schedule matched to each test date.
