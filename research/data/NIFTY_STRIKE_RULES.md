# NIFTY Weekly Strike-Interval Rule

NSE publishes a 50-point strike interval for NIFTY weekly and monthly index option contracts. The exact strategy's "near-ATM" rule therefore implies that, when the 09:30 underlying is available, the nearest listed strike should be no more than 25 points away in a complete surface.

Primary data-quality rule:
- select the listed strike nearest 09:30 NIFTY spot, with lower strike as a tie-break;
- if the source contains no selected strike within 25 points of spot for either initial leg, the date is excluded as an option-surface coverage failure rather than substituting a farther strike.

Source: NSE NIFTY 50 F&O strike interval page, which states an all-level 50-point interval for weekly/monthly contracts.
