# Cost Schedule — NIFTY Options

Primary sample: 2024-10-01 through 2025-12-31.

## Paytm Money
- F&O brokerage: Rs 10 per executed F&O order in the current public F&O FAQ.
- Count each leg open/close and each roll open/close as a separate executed order.

## NSE equity-option exchange + IPFT

The public NSE February 27, 2026 circular states that from March 1, 2026 the option-premium charge components are Rs 3,552/crore transaction charge plus Rs 0.01/crore IPFT, total Rs 3,553/crore per side. The same circular states the existing pre-March-2026 components were Rs 3,503/crore transaction charge plus Rs 50/crore IPFT, also Rs 3,553/crore total per side.

For the model, the **total exchange + IPFT outflow is Rs 35.53 per Rs 1 lakh of premium turnover per side** throughout the primary sample, while the component split changes on March 1, 2026. The components are retained in the code/config so the rate is auditable.

## STT
- 0.10% of option premium on option sales through March 31, 2026.
- 0.15% from April 1, 2026.

## Other levies
- SEBI turnover fee: 0.0001%.
- Stamp duty: 0.003% on option premium on buyer-side equity-option transactions.
- GST: 18% on brokerage + exchange/IPFT charges + SEBI turnover fee.

## Slippage
Primary: 1.0 option point adverse slippage per option-leg execution.
Sensitivity grid: 0.0, 0.5, 1.0, 2.0, 3.0, 5.0 points.

Signal and stop calculations use observed market prices before costs; slippage and statutory costs affect realized P&L only.
