# Gate P3 — Independent Contract / Point-in-Time Audit

**Tester branch:** `tester/phase-3-contract-validation`  
**Developer branch reviewed:** `developer/phase-3-contract-validation`  
**Review date:** 2026-10-05

## Independent evidence

Developer workflow run 23 completed successfully. Its committed summary reports:
- 311 option-source trade dates.
- 309 dates with a 09:30 spot observation.
- 2 deterministic missing-spot dates: 2024-11-01 and 2025-10-21.
- 8 historical lot-size transition dates excluded because the two strategy legs can have unequal contract lot sizes under the locked 100-point strategy-level stop definition.
- 301 eligible trade dates.
- 67 distinct current expiries and 67 distinct next expiries.
- 0 global duplicate-key groups and 0 duplicate rows.
- Completeness is measured rather than silently forward-filled.

## Tester checks

### 1. Expiry ordering
The developer query ranks distinct expiries on or after each trade date and assigns the first as current-week and the second as next-week. This is point-in-time and does not use future information beyond the listed expiry calendar.

**PASS.**

### 2. 09:30 strike selection
The selected CE and PE are ranked by absolute distance from the 09:30 spot and then strike ascending. This implements nearest strike with lower-strike tie break.

**PASS.**

### 3. Contract lot-size regimes
The corrected rules are:
- through 2024-12-26: 25;
- 2025-01-02 through 2025-12-30: 75;
- after 2025-12-30: 65.

The developer explicitly excludes dates where current and next legs have unequal lot sizes rather than inventing a conversion for the strategy-level 100-point stop.

**PASS.**

### 4. Duplicate-key integrity
The global validation groups by timestamp, expiry, strike and option type and reports zero duplicate groups / zero duplicate rows.

**PASS.**

### 5. Missing-bar treatment
The developer does not forward-fill. It records contract completeness and leaves execution-time handling to the Phase 4 engine.

**PASS, with required Phase 4 control:** every stop/adjustment/exit execution must fail closed when the required quote is unavailable.

### 6. Data-source limitation
The primary sample is explicitly frozen at 2024-10-01 through 2025-12-31. The tester agrees that the incomplete 2026 partition should not be mixed into the primary result.

**PASS.**

## Gate decision

**P3 = PASS, conditional on Phase 4 preserving the no-forward-fill rule.**

No strategy parameter changes are authorized from this gate.

## Instructions to developer

Proceed to Phase 4 only. Implement the deterministic event-driven engine and full Paytm Money cost ledger. Add unit tests for:
1. nearest-strike tie breaking;
2. current/next expiry mapping;
3. 50% trigger direction;
4. adjustment strike selection without look-ahead;
5. stop-loss precedence over adjustment;
6. next-bar execution;
7. 15:15 regular exit;
8. missing quote fail-closed behavior;
9. historical lot-size handling;
10. brokerage, STT, exchange charges, SEBI fee, GST, stamp duty and slippage accounting.

Do not optimize any parameter from P&L.
