# MARBTS Revised Paper Bundle

This bundle contains the revised IEEE-style paper source, paper figures, and
the checked-in MARBTS artifacts used for the numeric claims in the Results
section.

## Contents

- `main.tex` - revised paper source.
- `figures/` - architecture, workflow, result snapshots, and comparison plots.
- `data/` - JSON and Markdown reports copied from `artifacts/reports/` and
  selected metrics copied from `artifacts/metrics/`.

## Repository Verification Notes

- Multi-seed baseline was regenerated with the local `.venv` into `/tmp` using
  `PYTHONPATH=src .venv/bin/python scripts/run_multi_seed_report.py`.
- Policy matrix was regenerated with the local `.venv` into `/tmp` using
  `PYTHONPATH=src .venv/bin/python scripts/run_policy_experiment_matrix.py`.
- The paper avoids claims that are not implemented in the repo, including
  real exploit execution, active scan/monitor state mutation, and trained
  reinforcement-learning or LLM-backed policies.
- The prose was rewritten in original wording and external concepts are cited.
  No proprietary plagiarism detector was available in this environment, so this
  is not a certificate from Turnitin/iThenticate or similar tools.
