# Config Presets

Phase 6 runtime presets live here and are intended to remove ad-hoc command setup.

- `base/`: shared runtime defaults.
- `experiments/`: runnable preset files for experiment entry scripts and CLI commands.
- `seeds/`: curated deterministic seed bundles referenced by presets.

Usage pattern:

- Script mode:
  - `python scripts/run_multi_seed_report.py --config configs/experiments/multi_seed_baseline.json`
- Packaged CLI mode:
  - `marbts-multi-seed-report --config configs/experiments/multi_seed_baseline.json`
