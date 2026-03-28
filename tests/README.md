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
- Specific test file:
	- `python -m pytest tests/unit/test_environment_transitions.py -q`
- Specific test case:
	- `python -m pytest tests/unit/test_simulation_kernel.py::test_seed_reproducibility -q`

## Current Status

- Test framework: `pytest`
- Implemented coverage (Phase 1):
	- schema validation
	- graph initialization
	- transition primitives
	- legal action generation
	- simulation kernel and reproducibility
	- log artifact writing

## Contributor Notes

- Add tests near the related scope folder (`unit/`, `integration/`, `simulation/`, etc.).
- Prefer deterministic tests with fixed seeds for simulation behavior.
- If test workflow changes, update this README in the same change.

