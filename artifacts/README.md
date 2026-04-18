# Artifacts

Generated outputs only (never source-of-truth configs):

- `runs/`: run logs and event streams.
- `metrics/`: computed metric outputs.
- `figures/`: plots for analysis/papers.
- `reports/`: experiment summaries and evaluation bundles.

## Current Status

- Phase 1 smoke artifacts are generated under:
	- `runs/<run_id>/run_metadata.json`
	- `runs/<run_id>/timesteps.jsonl`
- Phase 2 policy telemetry artifact is generated under:
	- `runs/<run_id>/policy_metrics.json`
- Phase 2 baseline metrics artifact is generated under:
	- `metrics/<run_id>.json`
- Phase 2 multi-seed comparison report is generated under:
	- `reports/phase2_multi_seed_report_<scenario_id>.json`
- Phase 5 stress summary artifact is generated under:
	- `reports/phase5_stress_summary_<config_id>.json`
- Phase 5 decoy efficacy report is generated under:
	- `reports/phase5_decoy_efficacy_<scenario_id>.json`
- Phase 5 ablation bundle artifacts are generated under:
	- `reports/phase5_ablation_suite_<matrix_id>.json`
	- `reports/phase5_ablation_suite_<matrix_id>.md`
	- `reports/phase5_publication_table_<matrix_id>.json`
	- `reports/phase5_manifest_<matrix_id>.json`
- Phase 5 deception events are embedded in per-timestep run metrics under:
	- `runs/<run_id>/timesteps.jsonl`
- `figures/` remains scaffolded and currently contains a stub.

## Usage Notes

- Generate baseline run artifacts with:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase1_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase1_smoke.py`
- Generate Phase 2 rule-based run artifacts with dedicated policy metrics:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase2_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase2_smoke.py`
- Generate Phase 2 multi-seed aggregate report:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase2_multi_seed_report.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase2_multi_seed_report.py`
	- Custom seeds/horizon example:
		- `python scripts/run_phase2_multi_seed_report.py --seeds 20260329,20260330,20260331 --horizon 10`
	- Custom scenario/output roots example:
		- `python scripts/run_phase2_multi_seed_report.py --scenario scenarios/baselines/phase2_rule_baseline.json --runs-root artifacts/runs --metrics-root artifacts/metrics --reports-root artifacts/reports`
- Generate the initial Phase 5 stress suite:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase5_stress_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase5_stress_smoke.py`
- Generate the Phase 5 ablation bundle:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase5_ablation_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase5_ablation_smoke.py`
- Print the optional Phase 5 container reproduction command:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase5_container_command.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase5_container_command.py`
- Generated outputs in `runs/`, `metrics/`, `figures/`, and `reports/` are intended to remain local and are gitignored by default (except tracked `README.md` placeholders).
- Do not commit large generated artifacts unless explicitly needed for reproducibility evidence.
- If artifact layout changes, update this README in the same change.
