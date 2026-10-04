# Phase 4 Execution Rules

1. Entry is executed at the 09:30 local option-bar open for the initial near-ATM CE and PE.
2. Premium-ratio and stop-loss signals use completed one-minute bar closes.
3. Any signal observed at time t is executed at the next one-minute bar open.
4. Stop-loss has priority over an adjustment signal on the same observation.
5. An adjustment is not initiated from the 15:14 close because its execution would coincide with the mandatory 15:15 full-position exit; the 15:15 exit therefore takes precedence unless the 15:14 stop-loss was already hit.
6. The adjustment replacement strike is selected from same-expiry, same-option-type next-open quotes using premium-distance to the higher-premium leg's trigger-close premium, then point-in-time spot distance, then lower strike.
7. Point-in-time spot for an adjustment tie-break is the most recent 5-minute NIFTY spot observation at or before the execution timestamp; no future spot observation is used.
8. The stop-loss is evaluated in raw market-price points before slippage and fees.
9. Slippage and transaction costs affect realized P&L only, not signal generation.
10. Missing active-leg observations are never forward-filled. The event is skipped and counted as a monitoring gap. Missing required execution quotes (entry, adjustment, stop exit, or 15:15 exit) makes the trade unexecutable and excludes it from primary performance aggregates.
11. Re-entry is disabled because the user rule does not provide a deterministic re-entry condition.
12. Gross raw P&L is computed from raw market execution prices; net P&L subtracts realized slippage and the full transaction-cost ledger.
