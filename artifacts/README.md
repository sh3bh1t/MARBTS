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
- `metrics/`, `figures/`, and `reports/` are scaffolded and currently contain stubs.

## Usage Notes

- Generate baseline run artifacts with:
	- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase1_smoke.py`
	- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase1_smoke.py`
- Do not commit large generated artifacts unless explicitly needed for reproducibility evidence.
- If artifact layout changes, update this README in the same change.
