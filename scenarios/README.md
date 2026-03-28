# Scenarios

## Scope

This folder is the source of truth for simulation scenario inputs.

- `schemas/`: strict scenario schema references and versioning notes.
- `library/`: reusable experiment scenario catalog.
- `baselines/`: canonical baseline scenarios used for regression and smoke runs.

## Current Status

- Phase 1 baseline scenario available:
	- `baselines/minimal_valid.json`
- Example invalid scenario for validation testing:
	- `baselines/invalid_missing_security_level.json`
- `schemas/` and `library/` are scaffolded and currently contain stubs.

## Contributor Notes

- Any new scenario file must satisfy schema validation in `src/schemas/scenario.py`.
- Use semantic versioning in scenario metadata (`version`).
- If schema conventions change, update this README in the same change.
