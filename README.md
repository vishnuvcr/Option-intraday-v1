# Option-intraday-v1

Research repository for a reproducible backtest of the **Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put**.

## Research state

**Phase 2 underway — P1 passed; Phase 2 tester block remediated; rerun pending.**

The study is run as a gated quantitative research program with isolated developer/tester roles. The current locked plan and all status/error logs are version-controlled.

## Canonical documents

- [Research operating instructions](RESEARCH_INSTRUCTIONS.md)
- [Research plan](research/RESEARCH_PLAN.md)
- [Status](STATUS.md)
- [Research log](research/logs/RESEARCH_LOG.md)
- [Error log](research/logs/ERROR_LOG.md)
- [Conversation decision log](research/logs/CHAT_LOG.md)

## Strategy summary

At 09:30 IST:
1. Sell one near-ATM current-week NIFTY Call.
2. Sell one near-ATM next-week NIFTY Put.
3. Monitor both premiums intraday.
4. When one premium falls to approximately 50% of the other, roll the lower-premium leg to a strike with approximately matching premium.
5. Exit the complete position at 15:15 IST or earlier on the 100-option-point stop-loss.
6. Do not carry overnight.

The full deterministic operationalization is in [research/RESEARCH_PLAN.md](research/RESEARCH_PLAN.md) and [research/STRATEGY_SPEC.md](research/STRATEGY_SPEC.md).

## Data and cost policy

Public/free sources are preferred before paid sources. The planned primary intraday source is a public Hugging Face dataset pinned to an immutable revision; official NSE documents are used for contract/lot-size and levy reconciliation. Paytm Money brokerage, statutory levies, GST, and slippage are modeled separately so gross and net results can be distinguished.

## Current evidence

- P1 strategy freeze: passed independent tester re-audit.
- Phase 2 workflow: [.github/workflows/phase-2-data.yml](.github/workflows/phase-2-data.yml).
- Selected option source: public Hugging Face 1-minute NIFTY options.
- Selected spot source: public GitHub release with 5-minute NIFTY spot data through April 2026.
- Phase 3 validation: 296 eligible trade dates; 13 deterministic exclusions for spot availability, lot-size transition, and near-ATM source coverage.

## Research gates

P0 Governance → P1 Exact specification → P2 Data → P3 Validation → P4 Engine → P5 Backtest → P6 Robustness → P7 Independent tester → P8 OOS → P9 Manuscript.

No phase is promoted without the required gate evidence.
