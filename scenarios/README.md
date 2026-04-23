# Scenarios

## Scope

This folder is the source of truth for simulation scenario inputs.

- `schemas/`: strict scenario schema references and versioning notes.
- `library/`: reusable experiment scenario catalog.
- `baselines/`: canonical baseline scenarios used for regression and smoke runs.

## Current Status

- Phase 1 baseline scenario available:
	- `baselines/minimal_valid.json`
- Phase 2 baseline scenario available:
	- `baselines/rule_baseline.json`
- Example invalid scenario for validation testing:
	- `baselines/invalid_missing_security_level.json`
- Phase 2 library scenario seed added:
	- `library/containment_stress.json`
- Phase 5 library scenario added:
	- `library/scale_chain_6.json`
- Phase 5 scenario catalog manager added:
	- `src/schemas/catalog.py`
- Scenario catalog smoke command:
	- `python scripts/run_scenario_catalog_smoke.py`
- `schemas/` remains scaffolded and currently contains a stub.
- Scenario catalog support now covers semantic-versioned latest selection and taxonomy-aware grouping for research experiments.

## Contributor Notes

- Any new scenario file must satisfy schema validation in `src/schemas/scenario.py`.
- Use semantic versioning in scenario metadata (`version`).
- Scenario catalog indexing excludes test/invalid fixtures prefixed with `invalid_` by default.
- If schema conventions change, update this README in the same change.
