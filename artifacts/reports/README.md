# Reports Artifacts

This directory stores aggregated experiment reports and comparative summaries.

Current writer:
- `scripts/run_multi_seed_report.py`
- `scripts/run_policy_experiment_matrix.py`
- `scripts/run_comparative_report.py`
- `scripts/run_ablation_report.py`

Current output:
- `multi_seed_report_<scenario_id>.json`
- `policy_experiment_matrix_<scenario_id>.json`
- `policy_experiment_matrix_batch_<scenario_ids>.json`
- `comparative_report_<run_id_a>_vs_<run_id_b>.json`
- `comparative_report_<run_id_a>_vs_<run_id_b>.md`
- `../figures/comparative_report_<run_id_a>_vs_<run_id_b>_compromise_trend.svg`
- `../figures/comparative_report_<run_id_a>_vs_<run_id_b>_defense_efficiency.svg`
- `../figures/comparative_report_<run_id_a>_vs_<run_id_b>_response_latency.svg`
- `ablation/ablation_report_template_<package_id>.json`
- `ablation/ablation_report_template_<package_id>.md`
- `ablation/research_artifact_manifest_<package_id>.json`
- `ablation/container_execution_profile_<package_id>.json`

The report includes:
- aggregate statistics across seed runs
- aggregate stability bands (mean/stddev/min/max where applicable)
- deterministic consistency indicators (sequence-hash frequency and dominant-hash ratio)
- per-run run_id, sequence hash, and output artifact references
- condition-level comparisons for adaptive-vs-rule experiment matrices
- summary ranking views for lowest compromise, highest blue containment, and most deterministic conditions
- pairwise replay summaries for run-to-run comparisons
- markdown summaries with table views for compromise trend, defense efficiency, and response latency
- publication-style ablation tables with reproducibility metadata and optional container execution pins