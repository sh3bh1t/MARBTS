# Phase 1 Closure Hardening

Conforms to guide files in copilot/guides/

## Scope
This document defines closure hardening checks for Phase 1 implementation.

## Hardening Checks

1. **Schema Contract Integrity**
   - Scenario validation enforces required fields and explicit errors.
   - Negative-case tests verify malformed input rejection.

2. **State Transition Correctness**
   - Deterministic transition primitives tested: exploit, patch, isolate, block.
   - Unknown-node actions fail explicitly.

3. **Legal Action Safety Envelope**
   - Red/Blue legal action generation constrained to abstract action space.
   - Isolated-node restrictions and invalid-actor rejection covered.

4. **Determinism & Reproducibility**
   - Seeded RNG wrapper integrated in simulation kernel.
   - Same-seed run reproducibility validated by test trace equality.

5. **Logging Completeness**
   - Timestep logs include pre-state ref, red/blue intents, outcomes, post-state diff, metric delta.
   - Artifact writer persists run metadata and JSONL timestep stream.

6. **Smoke Execution Path**
   - Script: `scripts/run_phase1_smoke.py`
   - Produces run artifacts under `artifacts/runs/<run_id>/`.

## Recommended Closure Commands

- `e:/Coding/MARBTS/.venv/Scripts/python.exe -m pytest -q`
- `$env:PYTHONPATH='src'; e:/Coding/MARBTS/.venv/Scripts/python.exe scripts/run_phase1_smoke.py`

## Expected Evidence

- Pytest suite passes with all unit checks.
- Smoke script outputs `PHASE1_SMOKE_OK`.
- Generated files:
  - `artifacts/runs/<run_id>/run_metadata.json`
  - `artifacts/runs/<run_id>/timesteps.jsonl`

## Status

- Closure hardening scaffold implemented.
- Operational validation should be run as part of every Phase 1 completion gate.
