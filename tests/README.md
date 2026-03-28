# Tests

- `unit/`: schema validation, transition primitives, policy scoring units.
- `integration/`: environment-policy-orchestrator interactions.
- `simulation/`: end-to-end scenario loop behavior tests.
- `reproducibility/`: same-seed equivalence tests.
- `regression/`: stability checks for baseline scenarios.

## How To Run

- Full suite:
	- `e:/Coding/MARBTS/.venv/Scripts/python.exe -m pytest -q`
- Unit tests only:
	- `e:/Coding/MARBTS/.venv/Scripts/python.exe -m pytest tests/unit -q`
- Specific test file:
	- `e:/Coding/MARBTS/.venv/Scripts/python.exe -m pytest tests/unit/test_environment_transitions.py -q`
- Specific test case:
	- `e:/Coding/MARBTS/.venv/Scripts/python.exe -m pytest tests/unit/test_simulation_kernel.py::test_seed_reproducibility -q`

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

