# Conversation Decision Log

## 2026-10-05 — Backtest request

User requested: “Backtest this exact strategy in this repo” and provided the GitHub repository URL plus screenshots of the strategy reference sheet.

Relevant locked rules captured from the screenshots:
- 09:30 entry;
- sell current-week near-ATM Call;
- sell next-week near-ATM Put;
- no overnight position;
- monitor premiums;
- adjustment when one premium is approximately 50% of the other;
- move the lower-premium leg to a strike whose premium approximately matches the higher-premium leg;
- 100-point maximum-loss stop;
- exit entire position at 15:15;
- after stop-loss, the reference sheet mentions re-entry only when time/situation permits but does not define a deterministic re-entry rule.

Repository handling: implementation is governed by `RESEARCH_INSTRUCTIONS.md` and `research/RESEARCH_PLAN.md`. Private chain-of-thought is not recorded; only reproducible decision summaries are retained.

| 2026-10-05 | User: Resume / Proceed | Continued gated research from Phase 4 through Phase 9. Completed P4 engine gate, P5 primary backtest, P6 robustness, P7 independent reproduction, P8 chronological forward diagnostic, and P9 manuscript closure. Final primary result: -₹54,536.79 over 296 trades at 1-point slippage. Tester passed all gates. Research closed. |

| 2026-10-05 | User: Proceed after research closure | Verified the frozen P0–P9 evidence and synchronized the tester-passed Phase 9 release to `main`. No new strategy phase was started because the predefined stop condition closes this study. The main-branch README/STATUS metadata was corrected to match the closed state and the P9 tester audit was published on main. Any future strategy change must be a new research project. |

| 2026-10-05 | User: Proceed after research closure | Verified the frozen P0–P9 evidence and synchronized the tester-passed Phase 9 release to `main`. No new strategy phase was started because the predefined stop condition closes this study. The main-branch README/STATUS metadata was corrected to match the closed state and the P9 tester audit was published on main. Any future strategy change must be a new research project. |