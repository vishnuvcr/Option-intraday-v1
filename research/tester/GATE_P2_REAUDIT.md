# Gate P2 — Independent Data Acquisition / Validation Re-audit

**Tester branch:** `tester/phase-2-data`  
**Developer branch reviewed:** `developer/phase-2-data`  
**Review date:** 2026-10-05

## Evidence reviewed

- Phase 2 workflow run 40: successful end-to-end, including the post-job market-data cache save.
- Immutable Hugging Face revision: `78b1c5468255d18cf492984bfe6fe4e3ac874d7c`.
- Option partitions:
  - 2024: 14,592,609 rows; SHA-256 `573b6fa788dbe06cbb7f6c4a48ee2fcd259434ad05f70a1cca3e775bb5b9d934`.
  - 2025: 69,687,860 rows; SHA-256 `33c2525b57ba442cfabeaebfc63ace63d0292e8f69474d5ea1541b75c9546972`.
- Spot source: 92,876 rows; release asset SHA-256 `0c1f3de848a4e8c05e233c195685e7ae560d56d08df8baba8b2ffcfac699d3f8`.
- Validation report generated and uploaded as a workflow artifact.

## Independent checks

### Data schema / chronology

Pass:
- NIFTY underlying only.
- CE/PE option type only.
- 1-minute granularity.
- positive strikes.
- no negative OHLC values.
- OHLC high/low relationships valid.
- no unparseable trade dates or expiries.
- expiry never precedes trade date.
- option timestamp date matches trade date.
- all option timestamps are minute-boundary timestamps.
- no null option closes.
- no within-batch duplicate keys detected.

### Source-session contamination

The 2024 source contains 26,937 rows outside the 09:15–15:30 source-session window, equal to approximately 0.032% of all validated option rows. The developer does not feed these rows into strategy execution; the backtest is required to filter to the strategy-relevant intraday session.

**Pass with documented limitation.**

### 09:30 spot availability

Two dates lack a 09:30 spot observation:
- 2024-11-01
- 2025-10-21

The developer has explicitly excluded these dates from the primary strategy run because substituting another time or forward-filling would change the locked near-ATM rule.

**Pass with deterministic exclusions.**

### Source reproducibility

Pass:
- HF source is pinned to an immutable revision.
- file SHA-256 values are recorded.
- spot release is tag-pinned and SHA-256 checked.
- acquisition manifest is versioned in the repository.
- workflow has automatic and manual triggers.
- workflow concurrency is serialized so the data cache is not overwritten by overlapping runs.

### Coverage limitation

The HF NIFTY 2026 Kotak partition was found to be only 9,344 bytes and is excluded from the primary result. The primary sample is therefore frozen at 2024-10-01 through 2025-12-31. This is a reasonable reproducibility choice and must remain explicit in the final manuscript.

### Deferred item

A full global duplicate-key check is deferred to Phase 3 contract-level validation. This is acceptable because Phase 3 explicitly covers row/contract/expiry/strike/lot reconciliation.

## Gate decision

**P2 = PASS**

No change to the strategy specification was made in this gate.

## Tester isolation statement

The tester branch contains only the audit report. No implementation code has been supplied to the developer branch.

## Instructions to developer

Proceed to Phase 3 only. Build the contract/expiry/lot-size point-in-time reconciliation and contract-level duplicate/missing-minute validation. Preserve the current immutable data snapshot and all date exclusions. Do not alter the strategy rules or tune parameters based on preliminary P&L.
