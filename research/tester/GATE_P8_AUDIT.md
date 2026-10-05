# Gate P8 — Chronological Forward-Slice Audit

**Tester branch:** `tester/phase-8-oos-diagnostic`  
**Developer branch:** `developer/phase-8-oos-diagnostic`  
**Workflow:** 37304353703

## Audit

The developer correctly labels the split as a **retrospective chronological diagnostic**, not a prospectively sequestered OOS test. This distinction is scientifically important because the primary backtest had already been run over the full 2024-10-01–2025-12-31 sample.

Cutoff: **2025-07-01**.

### Development slice
- 175 trades
- net P&L: **−₹56,593.46**
- win rate: **56.00%**
- profit factor: **0.7721**
- max drawdown: **−₹74,643.93**

### Forward slice
- 121 trades
- net P&L: **+₹2,056.67**
- mean P&L/trade: **₹17.00**
- median: **₹239.30**
- win rate: **54.55%**
- profit factor: **1.0205**
- max drawdown: **−₹22,849.28**
- stop-loss trades: **0**
- adjustments: **170**

### Forward-slice slippage stress
- 0 points: **+₹63,796.67**
- 0.5 points: **+₹32,926.67**
- 1 point: **+₹2,056.67**
- 2 points: **−₹59,683.33**

The forward slice therefore barely remains positive at the primary 1-point slippage assumption and is highly friction-sensitive.

## Gate decision

**P8 = PASS WITH SCIENTIFIC QUALIFICATION.**

The calculation is internally consistent and the parameters were not changed. However, this must **not** be presented as prospective OOS validation in the final manuscript. It is a chronological forward-slice diagnostic discovered after the full-sample primary analysis.

## Instructions to developer

Proceed to Phase 9 manuscript and closure. Explicitly report:
1. the non-prospective nature of the forward slice;
2. the negative full-sample primary result;
3. the positive but fragile forward slice;
4. all cost/slippage sensitivity;
5. the limitations created by lack of a prospectively locked holdout;
6. no claim of live trading profitability.
