# Artifacts

Generated outputs only (never source-of-truth configs):

- `runs/`: run logs and event streams.
- `metrics/`: computed metric outputs.
- `figures/`: plots for analysis/papers.
- `reports/`: experiment summaries, evaluation bundles, and research artifact packages.

## Current Status

- Network core smoke artifacts are generated under:
	- `runs/<run_id>/run_metadata.json`
	- `runs/<run_id>/timesteps.jsonl`
- Rule baseline policy telemetry artifact is generated under:
	- `runs/<run_id>/policy_metrics.json`
- Baseline metrics artifact is generated under:
	- `metrics/<run_id>.json`
- Multi-seed comparison report is generated under:
	- `reports/multi_seed_report_<scenario_id>.json`
- Adaptive policy experiment matrix report is generated under:
	- `reports/policy_experiment_matrix_<scenario_id>.json`
- Batch matrix report is generated under:
	- `reports/policy_experiment_matrix_batch_<scenario_ids>.json`
- Pairwise comparative replay report is generated under:
	- `reports/comparative_report_<run_id_a>_vs_<run_id_b>.json`
	- `reports/comparative_report_<run_id_a>_vs_<run_id_b>.md`
	- `figures/comparative_report_<run_id_a>_vs_<run_id_b>_*.svg`
	- `figures/` now stores the comparison plots for compromise trend, defense efficiency, and response latency.
- Ablation report package artifacts are generated under:
	- `reports/ablation/ablation_report_template_<package_id>.json`
	- `reports/ablation/ablation_report_template_<package_id>.md`
	- `reports/ablation/research_artifact_manifest_<package_id>.json`
	- `reports/ablation/container_execution_profile_<package_id>.json` when containerized output is requested

## Usage Notes

- Generate network core smoke artifacts with:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_network_core_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_network_core_smoke.py`

- Generate rule baseline smoke artifacts with dedicated policy metrics:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_rule_baseline_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_rule_baseline_smoke.py`
- Generate multi-seed aggregate report:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_multi_seed_report.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_multi_seed_report.py`
	- Custom seeds/horizon example:
		- `python scripts/run_multi_seed_report.py --seeds 20260329,20260330,20260331 --horizon 10`
	- Custom scenario/output roots example:
		- `python scripts/run_multi_seed_report.py --scenario scenarios/baselines/rule_baseline.json --runs-root artifacts/runs --metrics-root artifacts/metrics --reports-root artifacts/reports`
- Generate adaptive planning smoke artifacts:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_adaptive_planning_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_adaptive_planning_smoke.py`
	- Custom seed/horizon example:
		- `python scripts/run_adaptive_planning_smoke.py`
- Generate adaptive policy experiment matrix reports:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_policy_experiment_matrix.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_policy_experiment_matrix.py`
	- Skip ablations example:
		- `python scripts/run_policy_experiment_matrix.py --skip-ablations`
	- Custom seeds/horizon example:
		- `python scripts/run_policy_experiment_matrix.py --seeds 20260423,20260424 --horizon 2`
- Generate batch matrix reports across scenarios:
	- `python scripts/run_policy_experiment_matrix.py --scenario-batch scenarios/baselines/rule_baseline.json,scenarios/library/containment_stress.json`
- Matrix reports include summary rankings for lowest compromise, highest blue containment, and most deterministic conditions.
- Generate pairwise comparative replay reports:
	- `python scripts/run_comparative_report.py --left-run-dir artifacts/runs/<run_id_a> --right-run-dir artifacts/runs/<run_id_b>`
- Generate ablation report packages:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_ablation_report.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_ablation_report.py`
- Generated outputs in `runs/`, `metrics/`, `figures/`, and `reports/` are intended to remain local and are gitignored by default (except tracked `README.md` placeholders).
- Do not commit large generated artifacts unless explicitly needed for reproducibility evidence.
- If artifact layout changes, update this README in the same change.
