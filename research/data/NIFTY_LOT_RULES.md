# NIFTY Weekly Option Lot-Size Rules Used in the Primary Sample

The primary sample ends on 2025-12-31, so only the 2024 and 2025 NIFTY weekly-contract lot-size regimes are needed.

| Weekly expiry date | Lot size |
|---|---:|
| On or before 2024-12-19 | 25 |
| 2024-12-26 through 2025-12-23 | 75 |

For any expiry after 2025-12-23 the primary sample does not use the contract.

Source basis: NSE index-derivatives lot-size circulars issued in October 2024 and October 2025. The implementation uses the expiry-date regime rather than assuming one constant lot size across the sample.

The 100-point strategy stop is converted to rupees as 100 × the lot size attached to the actual contracts used on that trade date.
