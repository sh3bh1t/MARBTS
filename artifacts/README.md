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
- Generated outputs in `runs/`, `metrics/`, `figures/`, and `reports/` are intended to remain local and are gitignored by default (except tracked `README.md` placeholders).
- Do not commit large generated artifacts unless explicitly needed for reproducibility evidence.
- If artifact layout changes, update this README in the same change.
