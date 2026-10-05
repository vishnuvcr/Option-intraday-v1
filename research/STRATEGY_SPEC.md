# Locked Strategy Specification

## Strategy

**Intraday Asymmetric Premium Strategy — Current-Week Call + Next-Week Put**

### User-provided rulebook

| Item | Rule |
|---|---|
| Entry | 09:30 IST |
| Current-week leg | Sell 1 near-ATM Call |
| Next-week leg | Sell 1 near-ATM Put |
| Monitoring | Intraday relative option-premium monitoring |
| Adjustment trigger | One premium becomes approximately 50% of the other |
| Adjustment | Move the lower-premium leg to a strike where its premium approximately equals the higher-premium leg; retain the other leg |
| Stop loss | 100 option points maximum loss; exit complete position |
| Regular exit | 15:15 IST |
| Overnight | None |
| Margin reference | ₹2.0–2.5 lakh |
| Re-entry | Reference sheet permits re-entry “if time and situation permits”, but supplies no deterministic trigger |

## Primary mechanical implementation

1. Underlying = NIFTY 50.
2. At 09:30 IST, find the closest available NIFTY spot/underlying observation.
3. Choose the nearest listed weekly expiry on or after the trade date as current-week, and the following listed weekly expiry as next-week.
4. Initial strike for each leg = available strike nearest the 09:30 underlying. Exact ties use the lower strike.
5. Initial execution = 09:30 candle **open** for both legs.
6. The strategy is entered only when both selected contracts have an executable 09:30 bar.
7. Every completed 1-minute bar after entry is treated as the observation point. A premium-ratio trigger is evaluated using that bar's close.
8. Trigger condition = lower premium / higher premium <= 0.50.
9. On a trigger, the lower-premium leg is closed and replaced at the next minute bar open by the same option type and same expiry at the strike whose next-bar-open premium is closest to the higher-premium leg's observed premium. Ties are resolved by strike distance to spot and then lower strike.
10. The other leg is retained.
11. Multiple adjustments are permitted when the trigger recurs.
12. Stop-loss is **one combined strategy-level maximum loss of 100 option-premium points × the applicable historical NIFTY lot size** for the complete two-leg position. It is computed from the original entry credit/debit plus all realized roll P&L and current mark-to-market across both legs. The trigger is evaluated from the observed bar close and executed at the next bar open. Stop-loss takes precedence over a simultaneous adjustment trigger.
13. Regular exit is the 15:15 bar open.
14. If the data end before the required exit, the trade is marked incomplete and excluded from primary performance aggregates rather than forward-filled.
15. Re-entry after stop-loss is **not enabled in the primary backtest** because the source rule does not define a deterministic re-entry trigger. This is a fidelity safeguard, not an optimization.
16. No look-ahead: strike selection for a future adjustment can use only prices actually available at the execution timestamp.
17. No forward-filling across missing option bars.

## Execution-cost model

Gross P&L and net P&L are both recorded.

Primary net-cost model:
- Paytm Money F&O brokerage: ₹10 per executed order based on the current public F&O FAQ; historical brokerage is stored as a versioned parameter and can be changed in sensitivity runs.
- STT, exchange transaction charges, SEBI fee, GST and stamp duty: calculated separately from the applicable historical rates in the cost table.
- Slippage: a versioned adverse option-price slippage parameter applied to each option execution. Primary slippage is **1.0 option point per contract leg per execution**; sensitivity uses a wider grid.
- The strategy rule itself is not optimized against the cost grid.

## Important specification ambiguity

The reference sheet uses the qualitative phrases “near ATM”, “approximately 50%”, and “approximately equal”. The above rules convert those phrases into fixed deterministic rules before looking at performance. The tester must verify that no result is obtained by changing these rules after inspecting P&L.
