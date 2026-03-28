# Reports Artifacts

This directory stores aggregated experiment reports and comparative summaries.

Current writer:
- `scripts/run_phase2_multi_seed_report.py`

Current output:
- `phase2_multi_seed_report_<scenario_id>.json`

The report includes:
- aggregate statistics across seed runs
- aggregate stability bands (mean/stddev/min/max where applicable)
- deterministic consistency indicators (sequence-hash frequency and dominant-hash ratio)
- per-run run_id, sequence hash, and output artifact references