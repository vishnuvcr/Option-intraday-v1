# Gate P4 — Independent Engine / Cost Audit

**Tester branch:** `tester/phase-4-engine-costs`  
**Developer branch reviewed:** `developer/phase-4-engine-costs`  
**Workflow:** 37251240866  
**Review date:** 2026-10-05

## Independent checks

### 1. Strategy timing and chronology — PASS
The engine enters at 09:30 open, observes completed 1-minute closes, executes trigger actions at the following minute open, gives stop-loss precedence over adjustment, exits at 15:15 open, and does not invent re-entry.

### 2. Initial strike selection — PASS
Nearest available strike to 09:30 spot is selected with deterministic lower-strike tie breaking.

### 3. Adjustment selection — PASS
The lower-premium leg is identified from the observed close. Replacement strike is selected using next-bar-open premium distance to the observed higher premium, then spot distance, then lower strike.

### 4. Stop-loss accounting — PASS
The combined 100-point stop is evaluated from original/rolled raw option-point P&L. Realized roll P&L is maintained in option points. Stop execution uses next-bar open.

### 5. Missing data — PASS
No forward-fill is used. Missing monitoring observations are recorded; missing required execution prices exclude the trade from completed aggregates.

### 6. Historical lot sizes — PASS
The frozen 25 / 75 / 65 expiry regimes are used, with unequal-leg transition dates excluded.

### 7. Cost ledger — PASS
Each execution records brokerage, STT, exchange charge, IPFT, SEBI fee, GST, stamp duty and slippage separately. Reconciliation:
**₹118,338.15 − ₹152,390.00 − ₹79,895.75 = −₹113,947.60.**

### 8. Unit tests — PASS
Workflow run reports **13/13 tests passed**.

## Result audit

301 eligible dates produced 301 completed trades and 0 unexecutable exclusions.

- Net P&L: **−₹113,947.60**
- Gross raw P&L: **₹118,338.15**
- Slippage: **₹152,390.00**
- Transaction costs: **₹79,895.75**
- Win rate: **54.49%**
- Profit factor: **0.721**
- Max drawdown: **−₹135,275.09**
- Stop-loss trades: **18**
- Trades with adjustment: **254**
- Total adjustments: **775**

## Gate decision

**P4 = PASS.**

This is an engine gate, not a final strategy-performance conclusion. No optimization is authorized from the P4 result.

## Instructions to developer

Proceed to Phase 5 only: freeze the primary ledgers, independently reconcile trade-level P&L/costs, produce primary statistical tables and equity/drawdown charts, document exclusions, and prepare the Phase 5 tester gate. Do not tune strategy parameters or begin robustness optimization before P5 passes.
