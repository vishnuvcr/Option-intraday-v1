# Research Status

**Repository:** `vishnuvcr/Option-intraday-v1`  
**Research target:** Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put  
**Date:** 2026-10-05

## Current phase

**Phase 4 — Engine/cost model: implementation starting after P3 pass**

| Phase | Status |
|---|---|
| 0 Governance | ✅ passed |
| 1 Strategy freeze | ✅ tester passed |
| 2 Data acquisition | ✅ tester passed |
| 3 Data validation | ✅ tester passed |
| 4 Engine/cost model | 🟡 implementation starting |
| 5 Primary backtest | ⚪ pending |
| 6 Robustness | ⚪ pending |
| 7 Independent tester | ⚪ pending |
| 8 OOS | ⚪ pending |
| 9 Manuscript | ⚪ pending |

## Immediate gate

P1 passed. Independent P2 audit blocked the data gate; developer remediated the listed reproducibility and validation defects. P2 passed. The primary reproducible sample is frozen at 2024-10-01 through 2025-12-31. Phase 3 is validating expiry ordering, historical lot-size regimes, initial contract availability, minute completeness, and global duplicate keys. The first runs exposed a manifest-field mismatch, an over-strict 346-minute completeness gate, and incorrect historical lot-size cutoffs. All three have been remediated. Workflow run 34 passed with 296 eligible trade dates and zero global duplicate-key groups after applying the NSE 50-point-grid near-ATM data-quality rule. Independent tester re-audit passed P3 with a no-forward-fill/fail-closed condition. Phase 4 is now authorized.

## Key known limitation

The user-provided rule says “re-entry if time and situation permits” but does not define a deterministic re-entry condition. The primary backtest will therefore not invent one. This is a specification limitation, not a model optimization.

## Data candidate

Public Hugging Face `rissin/nse-options-intraday` currently advertises NIFTY/BANKNIFTY/SENSEX 1-minute intraday coverage from October 2024 onward. Source provenance and license terms must be checked in Phase 2 before results are promoted.

## Cost candidate

Paytm Money's current public F&O FAQ states ₹10 brokerage per executed F&O order; statutory charges are separate and are applied from current official exchange/regulatory schedules with the historical schedule matched to each test date.
