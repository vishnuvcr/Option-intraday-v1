# Exact Strategy Backtest Research Plan

## Research question

**Does the locked intraday “Current-Week Call + Next-Week Put” asymmetric-premium strategy generate economically meaningful, reproducible NIFTY 50 option returns after realistic execution costs and Paytm Money charges over the available 1-minute historical sample?**

Secondary questions:
1. How often does the 50%-relative-premium adjustment trigger?
2. How often does the 100-option-point stop-loss trigger?
3. Is performance robust to execution friction, while keeping the primary strategy rule unchanged?
4. Are results stable across market regimes, weekdays, expiry proximity, and calendar periods?
5. Do results survive an untouched chronological holdout?

## Locked strategy specification to test

The primary backtest must implement the user-provided reference sheet without discretionary optimization:

- Underlying: NIFTY 50 index options.
- Entry: 09:30 IST.
- Initial current-week leg: sell 1 near-ATM Call.
- Initial next-week leg: sell 1 near-ATM Put.
- No overnight holding.
- Regular exit: close the complete position at 15:15 IST.
- Monitor option premiums intraday.
- Adjustment trigger: when the lower premium is approximately 50% of the higher premium.
- Adjustment action: move the lower-premium leg to a strike whose premium is approximately equal to the higher-premium leg, while retaining the other leg.
- Stop-loss: 100 option-premium points maximum loss for the complete position; exit the entire position when hit.
- Re-entry after stop-loss is permitted by the reference sheet only when time/situation permits. The primary implementation therefore treats re-entry as **disabled until a deterministic re-entry rule is present**, because adding a new discretionary rule would not be an exact test. This is logged as a specification limitation rather than silently invented.
- Margin reference: 2.0–2.5 lakh INR, used for capital-context reporting, not for return optimization.
- Position size: 1 lot per leg, using the historical contract lot size attached to the actual contract/expiry when available.

### Deterministic operationalization needed for reproducibility

Because the reference sheet uses qualitative language, the following mechanical conventions are frozen before the primary run:

1. “Near ATM” = strike nearest to NIFTY spot at 09:30; exact tie breaks to the lower strike.
2. “Current week” = nearest listed NIFTY 50 weekly expiry on/after the trade date.
3. “Next week” = the following listed weekly expiry.
4. Initial execution = 09:30 candle open, because minute OHLC data cannot identify a tick at 09:30:00.
5. Intraday monitoring = each completed 1-minute bar from 09:31 through 15:15. A trigger observed on bar close is executed at the next bar open to preserve chronology and avoid same-bar look-ahead.
6. Adjustment strike = among available strikes for the same option type and expiry, choose the strike with premium closest to the higher-premium leg at the next executable observation. If equally close, choose the strike closest to spot, then the lower strike.
7. Adjustment realization = close the old lower-premium leg and open the new strike as one roll; realized roll P&L is included in the trade P&L.
8. Stop-loss = cumulative mark-to-market loss from the original strategy entry plus realized roll P&L, measured in option points over the one-lot position pair. Because minute OHLC cannot establish intrabar sequencing, a stop triggered by a bar is executed at the next bar open in the primary chronological model.
9. If stop-loss and an adjustment condition occur on the same observed bar, stop-loss has priority.
10. Regular exit uses 15:15 candle open.
11. Missing/unexecutable quotes cause the leg to be marked unavailable; a trade is only entered when both required legs are executable. No forward-fill across missing intraday option observations.

## Scientific phases and gates

| Phase | Purpose | Gate |
|---|---|---|
| 0 | Governance, role isolation, plan, logs | P0: repo state and role model verified |
| 1 | Strategy freeze and executable rulebook | P1: tester confirms no discretionary rule remains |
| 2 | Market-data acquisition and source audit | P2: immutable dataset snapshot + source manifest |
| 3 | Data validation and contract/PIT reconciliation | P3: tester independently passes row, timestamp, expiry, strike and lot checks |
| 4 | Backtest engine + cost model | P4: deterministic unit/invariant tests pass |
| 5 | Primary exact-rule backtest | P5: complete trade ledger + reproducible aggregate results |
| 6 | Robustness and stress analysis | P6: no parameter selection using final holdout |
| 7 | Independent tester reproduction/audit | P7: tester report pass or blocking defects |
| 8 | Untouched chronological OOS / forward slice | P8: frozen parameters, no re-estimation |
| 9 | Manuscript, evidence package, conclusion | P9: complete manuscript and research closure |

## Statistical analysis

Primary:
- total and mean/median net P&L per trade;
- win rate;
- profit factor;
- annualized/period return on defined capital base;
- maximum drawdown;
- daily and trade-level Sharpe/Sortino where statistically sensible;
- skewness and kurtosis;
- VaR/Expected Shortfall diagnostics;
- bootstrap confidence interval for mean trade P&L;
- distribution of stop-loss and adjustment events.

Robustness:
- adverse slippage grid;
- cost grid;
- entry/exit execution convention stress;
- market-regime stratification;
- weekday and expiry-distance stratification;
- chronological train/validation/holdout comparison.

The primary rule is not re-optimized using these sensitivity results.

## Data hierarchy

Priority order:
1. NSE official / exchange-published data.
2. Publicly reproducible datasets derived from exchange data.
3. Public GitHub/Kaggle/Hugging Face sources with explicit provenance.
4. Composite data only when individual public sources have documented coverage gaps.

A current candidate source is the public Hugging Face `rissin/nse-options-intraday` dataset, which reports NIFTY 1-minute intraday option data from October 2024 onward and identifies Upstox as the intraday source. Official NSE contract/lot-size and levy schedules will be used to reconcile the strategy ledger.

## Deliverables

- machine-readable locked strategy specification;
- source/data manifest with hashes/revisions;
- acquisition/cache workflow;
- deterministic backtest engine;
- raw trade ledger;
- aggregate results tables and charts;
- error and research logs;
- tester gate reports;
- final manuscript and appendices.

## Stop condition

Research stops after Phase 9 unless a serious reproducibility defect requires remediation. Any future enhancement becomes a separately scoped research project rather than an unbounded extension of this study.
