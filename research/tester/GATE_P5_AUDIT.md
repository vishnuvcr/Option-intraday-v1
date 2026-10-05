# Gate P5 — Independent Primary Backtest Audit

**Tester branch:** `tester/phase-5-primary-backtest`  
**Developer branch:** `developer/phase-5-primary-backtest`  
**Workflow audited:** 37254411664 / subsequent corrected evidence workflow 37253765787  
**Review date:** 2026-10-05

## Gate checks

### Universe and ledger — PASS
- 296 eligible trade dates.
- 296 completed trades.
- 0 unexecutable exclusions.
- This matches Phase 3's frozen 296-date eligible universe.
- The previously invalid 301-date result is not used.

### P&L reconciliation — PASS
Trade-ledger net P&L independently sums to **−₹54,536.7864**.
Gross raw P&L − slippage − transaction costs reconciles exactly:
**₹127,063.40 − ₹134,540.00 − ₹47,060.1864 = −₹54,536.7864.**

### Execution-cost reconciliation — PASS
Execution ledger contains **2,040 executions** and total quantity **134,540**. With the locked 1.0 option-point adverse slippage per executed contract, slippage independently reconciles to **₹134,540**. Execution-level transaction costs sum to **₹47,060.1864**.

### Win rate and drawdown — PASS
Independent trade-ledger calculation gives:
- winning trades: **164 / 296 = 55.4054%**;
- cumulative net P&L: **−₹54,536.7864**;
- maximum drawdown: **−₹80,611.3624**.

These match the frozen statistics.

### Primary statistics — PASS
The frozen analysis reports:
- mean net P&L/trade: **−₹184.25**;
- median: **₹262.53**;
- profit factor: **0.8435**;
- stop-loss trades: **15**;
- adjustment trades: **249**;
- total adjustments: **428**;
- 95% bootstrap CI for mean trade P&L: **−₹522.01 to ₹153.38**;
- annualized daily Sharpe on ₹2 lakh reference capital: **−0.978**;
- annualized daily Sortino: **−1.165**;
- return on ₹2 lakh reference capital: **−27.27%**;
- return on ₹2.5 lakh reference capital: **−21.81%**.

### Monthly reconciliation — PASS
Monthly trade counts sum to 296 and monthly net P&L sums to **−₹54,536.7864**.

## Scientific interpretation at this gate

The frozen primary sample does **not** provide evidence of an economically profitable strategy after the locked 1-point-per-contract slippage and transaction-cost model. The nominal win rate above 50% is outweighed by loss magnitude/cost drag; profit factor is below 1. The bootstrap interval for mean trade P&L crosses zero, so the primary sample does not establish a statistically clear negative mean at the 95% bootstrap level either.

This is a descriptive primary result only. It does not justify parameter optimization.

## Gate decision

**P5 = PASS.**

Phase 6 robustness/stress analysis is authorized, with the strict condition that the primary rule remains unchanged and the robustness grid must not be used to select a preferred parameterization for the untouched OOS phase.

## Instructions to developer

Proceed to Phase 6:
1. keep the primary rule and 296-date primary sample frozen;
2. run pre-specified slippage/cost/execution-convention stress tests;
3. stratify by market regime, weekday and expiry proximity where data support it;
4. do not select parameters based on OOS data;
5. record every robustness result, including failures;
6. prepare a Phase 6 tester gate before any OOS work.
