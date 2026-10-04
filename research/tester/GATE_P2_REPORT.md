# Gate P2 — Independent Data Acquisition / Validation Audit

**Tester branch:** `tester/phase-2-data`  
**Developer branch reviewed:** `developer/phase-2-data`  
**Review date:** 2026-10-05

## Gate decision

**P2 = BLOCKED pending remediation.**

### T6 — Blocking: GitHub Actions expressions are escaped literally

The workflow currently contains `\${{ runner.os }}`, `\${{ hashFiles(...) }}`, and `\${{ secrets.HF_TOKEN }}`. Because the workflow file preserves the backslash, these are not the intended GitHub Actions expressions. This can break cache keying and prevent the HF secret from being injected.

**Required:** commit literal GitHub Actions expressions of the form `${{ ... }}` and verify the next run's logs show the cache and token-dependent acquisition step executing as intended.

### T7 — Blocking: HF source is not immutably pinned

The acquisition manifest records HF revision as `main`. That is mutable and cannot reproduce the same dataset later.

**Required:** resolve and record the exact dataset commit/revision used for each acquisition run, alongside file SHA-256 hashes.

### T8 — Blocking: data-quality gate is too weak for a trading backtest

Current validation checks schema, nonnegative OHLC, duplicate keys, and null close, but does not independently verify:
- timestamps parse as the intended Asia/Kolkata market time;
- option granularity is 1 minute;
- trading-session window;
- underlying is NIFTY;
- option types are CE/PE-equivalent valid values;
- positive strikes and sensible expiry dates;
- expiry is not before trade date;
- per-session timestamp ordering / duplicate-minute behavior;
- spot timestamp timezone and exact 09:30 availability;
- option/spot date overlap and day-level completeness.

These are material because the strategy depends on exact expiry ordering, 09:30 execution, and minute chronology.

**Required:** add deterministic validations and fail the gate on violations, with counts in the report.

### T9 — Material reproducibility issue: cost schedule needs source-level audit

The March-2026 NSE transaction/IPFT rate has a potential arithmetic/reporting ambiguity in the public circular. The current schedule collapses it to Rs 35.53/lakh without showing the separate transaction and IPFT components.

**Required:** preserve the exact official rate components in the cost schedule and compute the applied client-side rate transparently. Do not hide the ambiguity.

### T10 — Non-blocking: cache durability

Actions cache is useful but evictable. The canonical repository should retain manifests, hashes, code and results; the large raw dataset need not be committed. A later gate should ensure the exact dataset revision/hash is sufficient to reacquire the raw data.

## What passed

- Public-source-first hierarchy is appropriate.
- Exact spot release asset is SHA-256 pinned.
- Large data are not committed into Git history.
- Manual workflow dispatch exists.
- Paytm Money brokerage is parameterized separately from gross P&L.
- Source provenance is documented.

## Instructions to developer

Correct T6–T9, rerun the Phase 2 workflow, preserve all defects in the error log, and submit the resulting acquisition/validation evidence for independent re-audit. Do not build or run the performance engine until P2 passes.
