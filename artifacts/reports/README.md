# Reports Artifacts

This directory stores aggregated experiment reports and comparative summaries.

Current writer:
- `scripts/run_phase2_multi_seed_report.py`
- `scripts/run_phase3_adaptive_smoke.py`
- `scripts/run_phase3_llm_demo.py`
- `scripts/run_phase3_unified_demo.py`
- `scripts/run_phase4_demo.py`
- `scripts/run_phase4_report_from_artifacts.py`

Current output:
- `phase2_multi_seed_report_<scenario_id>.json`
- `phase3_adaptive_comparison_<scenario_id>.json`
- `phase3_unified_comparison_<scenario_id>.json`
- `phase4_demo_dashboard.html`
- `phase4_dashboard_from_artifacts.html`
- `phase4_comparison_from_artifacts.html`
- `phase4_replay_<run_id>.md`

The report includes:
- aggregate statistics across seed runs
- aggregate stability bands (mean/stddev/min/max where applicable)
- deterministic consistency indicators (sequence-hash frequency and dominant-hash ratio)
- per-run run_id, sequence hash, and output artifact references
- replay-oriented operator summaries and dashboard views for Phase 4 demo flows
- comparison trend views, action-mix summaries, and replay timeline tables in the Phase 4 HTML dashboard
- reusable report generation directly from existing run/report artifacts with strict validation
