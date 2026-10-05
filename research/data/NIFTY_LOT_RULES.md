# NIFTY Weekly Option Lot-Size Rules Used in the Primary Sample

The primary sample is 2024-10-01 through 2025-12-31.

| Expiry regime | NIFTY lot size |
|---|---:|
| Through 2024-12-26 weekly expiry | 25 |
| 2025-01-02 through 2025-12-30 weekly/monthly expiry | 75 |
| After 2025-12-30 | 65 |

NSE Circular 131/2024 identifies 19-Dec-2024 as the last weekly expiry with the existing lot size and 02-Jan-2025 as the first weekly expiry with the revised lot size. The 26-Dec-2024 weekly expiry therefore remains in the old regime. NSE Circular 176/2025 states that existing lot size remains applicable to weekly/monthly contracts through 30-Dec-2025 expiry, with the revised 65 lot thereafter.

Official NSE references:
- https://nsearchives.nseindia.com/content/circulars/FAOP64672.pdf
- https://nsearchives.nseindia.com/content/circulars/FAOP70616.pdf

If the two strategy legs have different historical lot sizes on a transition date, the primary engine excludes that date rather than inventing a conversion for the strategy-level 100-point stop.
