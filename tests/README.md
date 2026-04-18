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
- Adaptive policy tests:
	- `python -m pytest tests/unit/test_agents_adaptive.py -q`
- LLM integration tests:
	- `python -m pytest tests/integration/test_phase3_llm_report.py -q`
- Unified Phase 3 matrix tests:
	- `python -m pytest tests/integration/test_phase3_unified_report.py -q`
- Phase 4 replay/dashboard tests:
	- `python -m pytest tests/unit/test_phase4_artifact_loader.py tests/integration/test_phase4_demo_reports.py -q`
- Phase 4 strict validation/report reuse tests:
	- `python -m pytest tests/unit/test_phase4_validation_failures.py tests/integration/test_phase4_report_from_artifacts.py -q`
- Replay and event schema tests:
	- `python -m pytest tests/unit/test_simulation_replay_and_events.py -q`

## Current Status

- Test framework: `pytest`
- Implemented coverage (Phase 1 + Phase 2 completed):
	- schema validation
	- graph initialization
	- transition primitives
	- legal action generation
	- simulation kernel and reproducibility
	- log artifact writing
	- deterministic rule-based red/blue policy behavior
	- phase 2 action-sequence reproducibility and regression signature checks
	- phase 2 multi-seed aggregate report integration checks
	- adaptive planner legality and deterministic rollout behavior
	- OpenAI-backed adaptive policy legality checks and fallback handling
	- no-planning and reduced-observability ablations
	- run artifact validation, replay reconstruction, and richer HTML/Markdown reporting
	- explicit failure on event/provenance mismatch and report reuse from existing artifacts
	- event envelope validation and replay fidelity

## Contributor Notes

- Add tests near the related scope folder (`unit/`, `integration/`, `simulation/`, etc.).
- Prefer deterministic tests with fixed seeds for simulation behavior.
- If test workflow changes, update this README in the same change.
