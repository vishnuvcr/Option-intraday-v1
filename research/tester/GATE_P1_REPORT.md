# Gate P1 — Independent Strategy Specification Audit

**Tester branch:** `tester/phase-1-exact-strategy`  
**Developer branch reviewed:** `developer/phase-1-exact-strategy`  
**Review date:** 2026-10-05

## Scope

Independent audit of `research/STRATEGY_SPEC.md` and `config/strategy.json` against the user-provided screenshots, with emphasis on ambiguity, chronology, mathematics, and absence of post-hoc optimization.

## Findings

### T1 — Stop-loss unit is ambiguous and currently over-specified

The developer specification states:

> “100 option-premium points × the lot quantity in force for each leg”

That wording can be read as a 100-point threshold per leg, which would effectively double the strategy-level rupee threshold for the two-leg position. The reference sheet instead shows “100 points maximum loss” followed by “Nifty lot size × 100 = ₹6,500 per lot”, which is more consistent with **one 100-point maximum-loss threshold for the complete position**, not 100 points separately for each leg.

**Severity: Blocking.**

Required correction before P1 passes:
- Define the stop-loss as **one combined strategy-level 100-point loss threshold × the applicable lot size**, including realized roll P&L and current mark-to-market across both legs.
- Report the rupee threshold using the historical lot size for that contract set.
- Keep any alternative interpretation only as a sensitivity analysis, not as the primary result.

### T2 — Slippage convention is an assumption, not part of the user rule

The primary model uses 1.0 option point per execution. This is acceptable only if explicitly labeled as an execution-cost assumption rather than a strategy rule.

**Severity: Non-blocking.**

Required documentation:
- Keep gross results separate from net results.
- Identify the exact slippage model and run sensitivity rather than selecting it from performance.

### T3 — Re-entry is correctly not invented

The source permits re-entry “if time and situation permits” but provides no deterministic trigger. Disabling it in the primary exact-rule backtest is methodologically safer than inventing a discretionary rule.

**Severity: Pass.**

### T4 — Chronology handling is conservative

Observation at completed bar close and execution on the next bar open prevents same-bar look-ahead.

**Severity: Pass.**

### T5 — Initial strike and expiry selection are deterministic

Nearest strike to 09:30 underlying and nearest/second-nearest weekly expiry are reproducible. The tie-break is explicit.

**Severity: Pass.**

## Gate decision

**P1 = BLOCKED pending T1 correction.**

No performance backtest should be promoted until the developer changes the primary stop-loss definition and resubmits this gate for review.

## Independent tester position

I did not modify developer files or supply implementation code. This branch contains only the independent audit report.

## Instructions to developer

Correct T1 in the developer branch, update the research/error logs, and resubmit the strategy specification for an independent P1 re-audit. Do not proceed to data acquisition or performance tuning until the revised gate passes.
