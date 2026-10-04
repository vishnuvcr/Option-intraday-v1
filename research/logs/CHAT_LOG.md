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
