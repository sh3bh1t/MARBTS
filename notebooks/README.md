# Notebook Analysis Pack

This directory contains the Phase 6 Increment 3 reproducible notebook workflows.

## Notebook Set

- `replay_and_comparative_walkthrough.ipynb`
  - Regenerates baseline run artifacts (optional) and builds a pairwise comparative report from two runs.
- `policy_matrix_walkthrough.ipynb`
  - Regenerates policy matrix artifacts (optional) and analyzes condition rankings and deltas.
- `ablation_report_walkthrough.ipynb`
  - Regenerates ablation package artifacts (optional) and inspects publication tables plus reproducibility manifest fields.

## Usage

From repository root:

- Create/update artifacts using canonical presets:
  - `PYTHONPATH=src python scripts/run_multi_seed_report.py --config configs/experiments/multi_seed_baseline.json`
  - `PYTHONPATH=src python scripts/run_policy_experiment_matrix.py --config configs/experiments/policy_experiment_matrix_baseline.json`
  - `PYTHONPATH=src python scripts/run_ablation_report.py --config configs/experiments/ablation_report_baseline.json --containerized`
- Open notebooks with your preferred Jupyter frontend and execute cells in order.

Each notebook includes a `RUN_GENERATORS` flag. Keep it `False` to analyze existing artifacts, or switch to `True` to regenerate canonical inputs in-notebook.

## Validation

Run notebook asset smoke validation from repository root:

- `python scripts/run_notebook_smoke.py`

This verifies:
- notebook JSON structure,
- required MARBTS workflow metadata,
- expected code-cell content anchors for reproducible artifact generation.
