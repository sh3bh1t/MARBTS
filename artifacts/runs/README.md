# Run Artifacts

This directory stores per-run execution outputs generated locally.

Typical contents:
- `<run_id>/run_metadata.json`
- `<run_id>/initial_state.json`
- `<run_id>/final_state.json`
- `<run_id>/timesteps.jsonl`
- `<run_id>/events.jsonl`
- `<run_id>/policy_metrics.json`

All generated run outputs are gitignored by default.
Only this README is intended to be tracked.
