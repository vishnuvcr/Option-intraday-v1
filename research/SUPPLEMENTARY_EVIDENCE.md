# Supplementary Research Evidence

## Frozen primary artifacts

- PRIMARY_BACKTEST_SUMMARY.json — headline result.
- PRIMARY_STATISTICS.json — statistical diagnostics.
- PRIMARY_MONTHLY_RESULTS.csv — monthly performance.
- PRIMARY_EVENT_COUNTS_MONTHLY.csv — stop and adjustment counts.
- trade_ledger.csv — one row per completed trade.
- execution_ledger.csv — one row per executed action.

## Robustness artifacts

- ROBUSTNESS_COST_STRESS.csv
- ROBUSTNESS_WEEKDAY.csv
- ROBUSTNESS_LOT_REGIME.csv
- ROBUSTNESS_VOLATILITY_REGIME.csv
- ROBUSTNESS_SUMMARY.json

## Forward diagnostic

- OOS_FORWARD_DIAGNOSTIC.json
- OOS_FORWARD_COST_STRESS.csv

The forward diagnostic is retrospective and must not be described as prospective OOS validation.

## Independent audit

INDEPENDENT_AUDIT.json independently reconstructs the main ledger aggregates and verifies them against the frozen primary summary.

## Figures

- primary_equity_curve.png
- primary_drawdown.png
- primary_pnl_distribution.png

## Statistical caution

The bootstrap interval is a trade-level resampling diagnostic. It does not fully model serial dependence, regime persistence or market-state clustering.

## Reproduction principle

All headline results must trace to frozen ledgers and versioned code. The superseded 301-trade artifact is not valid primary evidence.
