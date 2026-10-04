# Research Log

| Step | Date | Phase | Action | Outcome | Evidence / next action |
|---|---|---|---|---|---|
| R-0001 | 2026-10-05 | 0 | Inspected project research context and the target repository. | Repository is empty; existing project research emphasizes PIT controls, data validation, realistic friction, CPCV/DSR/PBO, and explicit research gates. | Initialize this repository with its own strategy-specific plan and role separation. |
| R-0002 | 2026-10-05 | 0 | Reviewed the user-provided strategy reference screenshots. | Locked entry/exit, legs, adjustment, stop-loss, no overnight, margin context and rationale captured. | Freeze operational conventions before data acquisition. |
| R-0003 | 2026-10-05 | 0 | Checked public data availability. | A public Hugging Face dataset reports 1-minute NIFTY option data from Oct-2024 onward; official NSE sources exist for option contracts and levies. | Build a reproducible acquisition/cache workflow and reconcile contract metadata. |
| R-0004 | 2026-10-05 | 0 | Checked current Paytm Money F&O brokerage information. | Paytm Money public FAQ currently states ₹10 per executed F&O order; other public pages show that fees change over time. | Freeze the tested cost schedule with source date and keep brokerage separately parameterized for sensitivity. |
| R-0005 | 2026-10-05 | 1 | Independent P1 tester audit | Gate blocked on stop-loss unit ambiguity; developer corrected it to a single strategy-level 100-point threshold. | Resubmit unchanged rulebook for tester re-audit. |
| R-0006 | 2026-10-05 | 1 | P1 gate passed | Independent tester passed the corrected locked strategy specification. | Proceeded to Phase 2 data acquisition without changing strategy rules. |
| R-0007 | 2026-10-05 | 2 | Data acquisition architecture | Added public HF option-source acquisition, public 5-minute NIFTY spot release acquisition, hashes, validation, and an automated GitHub Actions workflow with cache + manual trigger. | Triggered Phase 2 workflow is the next evidence source. |
| R-0008 | 2026-10-05 | 2 | Independent P2 audit | Tester blocked the data gate on workflow-expression escaping, mutable HF revision, insufficient chronology/contract validation, and cost-component transparency. | Developer remediated T6-T9 on the dedicated Phase 2 branch; rerun is required before P2 can pass. |
