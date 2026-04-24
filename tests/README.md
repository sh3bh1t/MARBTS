# Tests

- `unit/`: schema validation, transition primitives, policy scoring units.
- `integration/`: environment-policy-orchestrator interactions.
- `simulation/`: end-to-end scenario loop behavior tests.
- `reproducibility/`: same-seed equivalence tests.
- `regression/`: stability checks for baseline scenarios.

## How To Run

Assumption: run from repository root with your Python environment activated.

If you have not set up the environment yet:
- `python -m venv .venv`
- PowerShell: `.venv\Scripts\Activate.ps1`
- Bash/Zsh: `source .venv/bin/activate`
- `python -m pip install -r requirements.txt`

- Full suite:
	- `python -m pytest -q`
- Unit tests only:
	- `python -m pytest tests/unit -q`
- Reproducibility tests only:
	- `python -m pytest tests/reproducibility -q`
- Regression tests only:
	- `python -m pytest tests/regression -q`
- Specific test file:
	- `python -m pytest tests/unit/test_environment_transitions.py -q`
- Specific test case:
	- `python -m pytest tests/unit/test_simulation_kernel.py::test_seed_reproducibility -q`
- Adaptive policy unit coverage:
	- `python -m pytest tests/unit/test_agents_adaptive.py -q`
- Phase 3 matrix integration coverage:
	- `python -m pytest tests/integration/test_policy_experiment_matrix.py -q`
- Phase 3 matrix batch integration coverage:
	- `python -m pytest tests/integration/test_policy_experiment_matrix_batch.py -q`
- Phase 5 stress suite integration coverage:
	- `python -m pytest tests/integration/test_stress_test_suite.py -q`
- Preset loading and packaged command-layer coverage:
	- `python -m pytest tests/unit/test_runtime_presets.py tests/unit/test_marbts_cli_experiment_commands.py -q`
- Container runtime asset/spec coverage:
	- `python -m pytest tests/unit/test_container_runtime_assets.py -q`
- Observability serialization and validation coverage:
	- `python -m pytest tests/unit/test_simulation_logging_artifacts.py tests/unit/test_observability_validation.py -q`
- Observability replay and comparative report coverage:
	- `python -m pytest tests/unit/test_observability_replay.py tests/unit/test_visualization_comparative_report.py -q`
	- Covers replay reconstruction, comparative summary packaging, markdown report generation, and SVG figure outputs.
- Scenario catalog registry coverage:
	- `python -m pytest tests/unit/test_scenario_catalog.py -q`
- Adaptive decoy/bluff hook coverage:
	- `python -m pytest tests/unit/test_agents_adaptive.py -q`
- Ablation report package coverage:
	- `python -m pytest tests/unit/test_ablation_report.py -q`
- Notebook asset validation coverage:
	- `python -m pytest tests/unit/test_notebook_assets.py -q`

## Current Status

- Test framework: `pytest`
- Implemented coverage (Phase 1 + Phase 2 completed, Phase 3 completed, Phase 4 completed, Phase 5 increments 1-4 completed):
	- schema validation
	- graph initialization
	- transition primitives
	- legal action generation
	- simulation kernel and reproducibility
	- log artifact writing with provenance envelopes
	- deterministic rule-based red/blue policy behavior
	- phase 2 action-sequence reproducibility and regression signature checks
	- phase 2 multi-seed aggregate report integration checks
	- adaptive planning policy determinism, safety-filter rejection, and rationale trace payload emission
	- phase 3 experiment matrix generation with adaptive-vs-rule conditions, ablation-labeled outputs (including deception-enabled variants), and batch scenario ranking views
	- observability schema validation and provenance capture
	- replay bundle loading and comparative report packaging
	- comparative trend plots, defense-efficiency summaries, and response-latency visualizations
	- semantic-versioned scenario catalog generation and latest-version selection logic
	- adaptive decoy/bluff hook scoring and deception event rationale payload emission
	- stress-suite profile orchestration for scale/noise/observability experiments
	- ablation report package generation with research manifest and optional container profile output
	- phase 6 docker runtime asset/spec validation and container-profile command dispatch dry-run execution
	- phase 6 notebook asset validation and scaffold-removal coverage

## Contributor Notes

- Add tests near the related scope folder (`unit/`, `integration/`, `simulation/`, etc.).
- Prefer deterministic tests with fixed seeds for simulation behavior.
- If test workflow changes, update this README in the same change.
- Phase 6 presetized script defaults:
	- `python scripts/run_multi_seed_report.py --config configs/experiments/multi_seed_baseline.json`
	- `python scripts/run_policy_experiment_matrix.py --config configs/experiments/policy_experiment_matrix_baseline.json`
	- `python scripts/run_stress_test_suite.py --config configs/experiments/stress_test_suite_baseline.json`
	- `python scripts/run_ablation_report.py --config configs/experiments/ablation_report_baseline.json`
	- `python scripts/run_container_profile.py --spec multi_seed_baseline --dry-run`
	- `python scripts/run_notebook_smoke.py`
