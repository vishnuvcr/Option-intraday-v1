# Research Status

**Repository:** `vishnuvcr/Option-intraday-v1`  
**Research target:** Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put  
**Date:** 2026-10-05

## Current phase

**Phase 9 — Manuscript and research closure: complete; tester passed.**

| Phase | Status |
|---|---|
| 0 Governance | ✅ passed |
| 1 Strategy freeze | ✅ tester passed |
| 2 Data acquisition | ✅ tester passed |
| 3 Data validation | ✅ tester passed |
| 4 Engine/cost model | ✅ tester passed |
| 5 Primary backtest | ✅ tester passed |
| 6 Robustness | ✅ tester passed |
| 7 Independent tester | ✅ reproduction audit passed |
| 8 OOS | ✅ tester passed with non-prospective qualification |
| 9 Manuscript | ✅ complete; tester passed |

## Frozen primary evidence

- Primary window: **2024-10-01 through 2025-12-31**
- Completed trades: **296**
- Gross raw P&L: **₹127,063.40**
- Slippage: **₹134,540.00**
- Transaction costs: **₹47,060.19**
- Net P&L: **−₹54,536.79**
- Win rate: **55.41%**
- Profit factor: **0.844**
- Maximum drawdown: **−₹80,611.36**
- Primary slippage: **1.0 option point per executed contract**
- Approximate break-even adverse slippage: **0.59 points per executed contract**

## Scientific qualification

The July–December 2025 chronological forward slice was **+₹2,056.67** at 1-point slippage, but the split was formalized after the full-sample primary analysis. It is therefore a retrospective diagnostic, **not prospective out-of-sample validation**.

The primary conclusion is that the locked strategy is **not validated as a robust profitable strategy after realistic execution costs**.

## Closure

P0–P9 are complete. The final manuscript, supplementary evidence, ledgers, robustness results, forward diagnostic, independent audit, and P9 tester report are committed to the repository.

Research is **closed under the predefined Phase 9 stop condition**. No parameter search or strategy modification should be performed inside this study.

Any future strategy modification must begin as a separately scoped research project with a new frozen specification, independent developer/tester branches, and fresh gates.
