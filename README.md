# Option-intraday-v1

Research repository for a reproducible backtest of the **Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put**.

## Research state

**Phase 9 complete — tester passed; research closed.**

The study was run as a gated quantitative research program with isolated developer/tester roles. The frozen plan, evidence, tester reports, error log, and research decision log are version-controlled.

## Canonical documents

- [Research operating instructions](RESEARCH_INSTRUCTIONS.md)
- [Research plan](research/RESEARCH_PLAN.md)
- [Status](STATUS.md)
- [Research log](research/logs/RESEARCH_LOG.md)
- [Error log](research/logs/ERROR_LOG.md)
- [Conversation decision log](research/logs/CHAT_LOG.md)
- [Final manuscript](research/FINAL_MANUSCRIPT.md)
- [Final tester audit](research/tester/GATE_P9_AUDIT.md)

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

Public/free sources were preferred before paid sources. The primary intraday source is a pinned public Hugging Face dataset revision; official NSE documents were used for contract/lot-size and levy reconciliation. Paytm Money brokerage, statutory levies, GST, and slippage were modeled separately so gross and net results remain distinguishable.

## Final research evidence

- [Final manuscript](research/FINAL_MANUSCRIPT.md)
- [Supplementary evidence](research/SUPPLEMENTARY_EVIDENCE.md)
- [Primary statistics](research/results/PRIMARY_STATISTICS.json)
- [Primary trade ledger](research/results/trade_ledger.csv)
- [Execution ledger](research/results/execution_ledger.csv)
- [Robustness results](research/results/ROBUSTNESS_SUMMARY.json)
- [Forward diagnostic](research/results/OOS_FORWARD_DIAGNOSTIC.json)
- [Independent audit](research/results/INDEPENDENT_AUDIT.json)
- [P9 tester audit](research/tester/GATE_P9_AUDIT.md)

**Primary conclusion:** the strategy is not validated as a robust profitable strategy after realistic execution costs. The later forward slice was slightly positive but was not prospectively sequestered and is therefore only a retrospective diagnostic.

## Final status

- P0–P9 gates: complete.
- Primary validated window: 2024-10-01 through 2025-12-31.
- Primary completed trades: 296.
- Primary net P&L: **−₹54,536.79** under 1-point adverse slippage.
- Independent tester: **P9 passed**.
- Research: **closed** under the predefined Phase 9 stop condition.

## Research gates

P0 Governance → P1 Exact specification → P2 Data → P3 Validation → P4 Engine → P5 Backtest → P6 Robustness → P7 Independent tester → P8 OOS → P9 Manuscript.

No phase is promoted without the required gate evidence. Any future strategy modification must start as a separately scoped research project with a new frozen specification and independent tester gates.
