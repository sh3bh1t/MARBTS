# Scenario Schemas

This directory stores schema governance notes for scenario inputs.

Current implementation state:
- runtime validation is enforced by `src/schemas/scenario.py`
- scenario catalog validation is enforced by `src/experiments/scenario_catalog.py`

Current schema expectations:
- scenario root contains `metadata`, `nodes`, and `edges`
- `metadata` must include semantic `version`
- catalog entries must match the referenced scenario file `scenario_id` and `version`

If scenario schema behavior changes, update this README and the validator implementation in the same change.
