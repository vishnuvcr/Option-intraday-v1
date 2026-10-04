# Gate P3 — Independent Contract / Point-in-Time Re-audit

**Tester branch:** `tester/phase-3-contract-validation`  
**Developer branch reviewed:** `developer/phase-3-contract-validation`  
**Review date:** 2026-10-05

## Independent evidence

Developer workflow run 34 completed successfully. The current artifact reports:
- 311 option-source trade dates.
- 309 dates with a 09:30 spot observation.
- 2 deterministic missing-spot dates: 2024-11-01 and 2025-10-21.
- 8 dates excluded because the two strategy legs have unequal historical lot sizes.
- 5 additional dates excluded because the option source lacks a valid near-ATM next-week PE within 25 NIFTY points of the 09:30 spot.
- 296 eligible trade dates.
- 67 distinct current expiries and 67 distinct next expiries.
- 0 global duplicate-key groups and 0 duplicate rows.
- Completeness is measured rather than silently forward-filled.

## Tester checks

### 1. Expiry ordering

The developer query ranks distinct expiries on or after each trade date and assigns the first as current-week and the second as next-week.

**PASS.**

### 2. 09:30 strike selection

The selected CE and PE are ranked by absolute distance from the 09:30 spot and then strike ascending, implementing nearest strike with lower-strike tie break.

**PASS.**

### 3. Near-ATM source coverage

NSE publishes a 50-point strike interval for NIFTY weekly/monthly contracts. The nearest listed strike in a complete chain should therefore be at most 25 points from spot.

Five dates had a next-week PE source gap that previously forced selection of a strike thousands of points away from spot. The developer now excludes those dates rather than silently trading a far-away strike.

**PASS.**

### 4. Contract lot-size regimes

The corrected rules are:
- through 2024-12-26: 25;
- 2025-01-02 through 2025-12-30: 75;
- after 2025-12-30: 65.

The developer excludes dates where current and next legs have unequal lot sizes rather than inventing a conversion for the strategy-level 100-point stop.

**PASS.**

### 5. Duplicate-key integrity

The global validation groups by timestamp, expiry, strike and option type and reports zero duplicate groups / zero duplicate rows.

**PASS.**

### 6. Missing-bar treatment

The developer does not forward-fill. It records contract completeness and leaves execution-time handling to the Phase 4 engine.

**PASS, with required Phase 4 control:** every stop/adjustment/exit execution must fail closed when the required quote is unavailable.

### 7. Data-source limitation

The primary sample remains frozen at 2024-10-01 through 2025-12-31. The incomplete 2026 partition remains outside the primary result.

**PASS.**

## Gate decision

**P3 = PASS, conditional on Phase 4 preserving the no-forward-fill rule.**

No strategy parameter changes are authorized from this gate.

## Instructions to developer

Proceed to Phase 4 only. Implement the deterministic event-driven engine and full Paytm Money cost ledger. Add unit tests for nearest-strike tie breaking, current/next expiry mapping, 50% trigger direction, no-look-ahead adjustment selection, stop-loss precedence, next-bar execution, 15:15 exit, missing-quote fail-closed behavior, historical lot-size handling, and all brokerage/statutory/slippage accounting. Do not optimize any parameter from P&L.
