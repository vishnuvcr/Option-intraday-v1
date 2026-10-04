# Research Operating Instructions

This repository implements the intraday options research program requested for **Option-intraday-v1**.

## Mandatory operating rules

1. Treat the GitHub repository as the canonical research state.
2. Preserve the locked strategy specification before any performance optimization.
3. Maintain separate, isolated **developer** and **tester** branches. The tester must independently audit the developer work and must not contribute implementation code to the developer branch.
4. Use explicit research gates. The developer may not advance past a gate until an independent tester report says the gate passed or records an explicit blocking defect.
5. Record every implementation/research error in `research/logs/ERROR_LOG.md`.
6. Record every completed research step and its outcome in `research/logs/RESEARCH_LOG.md`.
7. Keep the detailed plan in `research/RESEARCH_PLAN.md`. Change the plan only when the research design itself changes.
8. Keep `STATUS.md` and `README.md` synchronized with the latest research state and link to canonical research documents.
9. Preserve source manifests, dataset hashes/revisions, code versions, parameters, cost assumptions, and execution assumptions so results are reproducible.
10. Include realistic execution friction: slippage, Paytm Money brokerage, statutory charges, exchange/SEBI fees, GST, and stamp duty where the required historical rate can be established. Report gross and net results separately.
11. Prefer free/public data first. Document failed sources and use composite datasets only when source coverage gaps require it.
12. Stop when the defined research phases are complete; do not expand the research indefinitely.
13. The final deliverable must contain a structured research manuscript with methods, results, tables, charts, limitations, conclusion, and future work.

## Conversation logging

The repository may record concise summaries of user requests, decisions, assumptions, tool/data outcomes, and research actions. Private chain-of-thought is not stored; only reproducible decision records and concise conversation summaries belong in the repository.

## Developer/tester role lock

- `developer/*`: implementation, data engineering, experiment execution, defect remediation.
- `tester/*`: independent validation, mathematical/logical review, leakage audit, data reconciliation, reproduction checks, and gate reports.
- These role definitions must not be swapped.

Last governance revision: 2026-10-05.
