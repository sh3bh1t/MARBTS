# Reports Artifacts

This directory stores aggregated experiment reports and comparative summaries.

Current writer:
- `scripts/run_multi_seed_report.py`
- `scripts/run_policy_experiment_matrix.py`
- `scripts/run_comparative_report.py`

Current output:
- `multi_seed_report_<scenario_id>.json`
- `policy_experiment_matrix_<scenario_id>.json`
- `policy_experiment_matrix_batch_<scenario_ids>.json`
- `comparative_report_<run_id_a>_vs_<run_id_b>.json`

The report includes:
- aggregate statistics across seed runs
- aggregate stability bands (mean/stddev/min/max where applicable)
- deterministic consistency indicators (sequence-hash frequency and dominant-hash ratio)
- per-run run_id, sequence hash, and output artifact references
- condition-level comparisons for adaptive-vs-rule experiment matrices
- summary ranking views for lowest compromise, highest blue containment, and most deterministic conditions
- pairwise replay summaries for run-to-run comparisons