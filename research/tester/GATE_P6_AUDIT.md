# Gate P6 — Independent Robustness / Stress Audit

**Tester branch:** `tester/phase-6-robustness`  
**Developer branch:** `developer/phase-6-robustness`  
**Workflow:** 37303715866  
**Review date:** 2026-10-05

## Checks

### Cost/slippage stress — PASS
The frozen primary ledger was stress-tested without changing strategy rules:
- 0.0-point slippage: **+₹80,003.21**
- 0.5-point slippage: **+₹12,733.21**
- 1.0-point slippage: **−₹54,536.79** (primary)
- 2.0-point slippage: **−₹189,076.79**
- 3.0-point slippage: **−₹323,616.79**

Transaction-cost multiplier stress also remains negative at the primary 1-point slippage:
- 0× costs: **−₹7,476.60**
- 0.5×: **−₹31,006.69**
- 1×: **−₹54,536.79**
- 1.5×: **−₹78,066.88**
- 2×: **−₹101,596.97**

The stress calculations reconcile directly to the frozen gross P&L, execution quantity, and transaction-cost ledger. No re-optimization was performed.

### Weekday stratification — PASS
The analysis is descriptive and pre-specified. The single Saturday trade is **2025-02-01**, a special Indian market session, not a data parsing error. It must not be interpreted as ordinary Saturday trading.

### Lot-regime stratification — PASS
The 25/75/65 historical lot regimes are preserved. The single 65-lot observation is the final 2025-12-31 contract regime and is reported rather than removed.

### Volatility regime — PASS
A pre-specified 20-trading-day realized-volatility measure from 09:30 NIFTY observations was split at the sample median:
- median cut: **11.127% annualized**
- 148 trades in each regime;
- HIGH_VOL net P&L: **−₹40,531.26**
- LOW_VOL net P&L: **−₹14,005.52**

This is a descriptive regime split; it is not used for parameter selection.

## Important inference

The primary result is strongly friction-sensitive. The locked 1-point slippage assumption changes the aggregate result from positive at 0.5 points to negative at 1 point. The approximate break-even adverse slippage is therefore around **0.59 points per executed contract**, before any additional model changes. Because the primary rule is not optimized to this threshold, this is a robustness finding rather than a tuning recommendation.

The strategy remains negative under all tested transaction-cost multipliers at the primary 1-point slippage.

## Gate decision

**P6 = PASS.**

No robustness result authorizes parameter changes. The untouched chronological OOS phase may proceed with the primary parameters frozen exactly as specified.

## Instructions to developer

Proceed to Phase 7/8 with:
1. primary parameters frozen;
2. no use of OOS data for tuning;
3. clearly separated in-sample/primary and untouched OOS evidence;
4. reproduce the strategy independently on the OOS period;
5. include all costs and slippage;
6. record every failure and mismatch.
