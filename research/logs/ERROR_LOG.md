# Error Log

| ID | Date | Phase | Severity | Error / observation | Root cause | Resolution | Status |
|---|---|---|---|---|---|---|---|
| E-0001 | 2026-10-05 | 0 | Medium | The target GitHub repository is currently empty despite having a default branch named `main`. | Repository was newly created without source files. | Initialize governance files before creating isolated developer/tester branches. | Open/mitigated |

New defects must be appended; do not overwrite historical entries.

| E-0002 | 2026-10-05 | 1 | Blocking | Tester found that the initial stop-loss wording could be interpreted as 100 points per leg, conflicting with the reference sheet's strategy-level 100-point loss indication. | Ambiguous wording in initial operationalization. | Revised primary definition to one combined strategy-level 100-point threshold × applicable lot size; re-entry remains disabled because no deterministic rule exists. | Resolved |
