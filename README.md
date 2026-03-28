# MARBTS

Sandboxed Red vs Blue Autonomous Cyber Defense Simulation System

## Project Overview
MARBTS is a research-grade autonomous cyber defense simulation platform designed for controlled, explainable, and reproducible Red vs Blue experimentation.

The system models attacker-defender dynamics in a synthetic graph-based network and is intentionally sandboxed:
- no real exploit frameworks,
- no live target interaction,
- no unsafe operational tooling.

Primary design goals:
- **Modularity**: replaceable environment, agent, simulation, logging, and experiment components
- **Explainability**: every agent action includes rationale and expected effect
- **Reproducibility**: deterministic seeded execution and run provenance capture
- **Research utility**: supports baseline comparisons, adaptive-policy experiments, and ablations

## Shared Foundation Layer (`src/hart`)

`src/hart` is the centralized, reusable foundation for cross-cutting contracts and portable shared logic.

- `src/hart/enums/`: canonical enum vocabularies (actors, actions, node states, etc.)
- `src/hart/models/`: canonical dataclass models/contracts used across schema, environment, and simulation modules

Design intent:
- prevent duplicate contract definitions,
- keep imports consistent across modules,
- make shared logic easier to reuse for future hosted/online services and tooling.

## Source of Truth and Governance
Authoritative planning and execution constraints are defined in:
- `.agent/guides/project_principles.md`
- `.agent/guides/execution_rules.md`
- `.agent/guides/testing_and_validation.md`

Implementation roadmap and phase plans are defined in:
- `.agent/plans/master_plan.md`
- `.agent/plans/phase_1_network_simulation.md`
- `.agent/plans/phase_2_agents_rule_based.md`
- `.agent/plans/phase_3_autonomy_llm_rl.md`
- `.agent/plans/phase_4_logging_visualization.md`
- `.agent/plans/phase_5_advanced_research.md`

## Repository Structure

```text
MARBTS/
├─ README.md
├─ .agent/
│  ├─ guides/
│  └─ plans/
├─ src/
│  ├─ hart/
│  │  ├─ enums/
│  │  └─ models/
│  ├─ core/
│  ├─ environment/
│  ├─ agents/
│  │  ├─ interfaces/
│  │  ├─ red/
│  │  ├─ blue/
│  │  └─ adaptive/
│  ├─ simulation/
│  ├─ schemas/
│  ├─ logging/
│  ├─ metrics/
│  ├─ experiments/
│  ├─ visualization/
│  └─ utils/
├─ tests/
│  ├─ unit/
│  ├─ integration/
│  ├─ simulation/
│  ├─ reproducibility/
│  └─ regression/
├─ scenarios/
│  ├─ schemas/
│  ├─ library/
│  └─ baselines/
├─ configs/
│  ├─ base/
│  ├─ experiments/
│  └─ seeds/
├─ scripts/
├─ docs/
│  ├─ architecture/
│  ├─ operations/
│  └─ research/
├─ artifacts/
│  ├─ runs/
│  ├─ metrics/
│  ├─ figures/
│  └─ reports/
├─ notebooks/
├─ docker/
└─ idea-core/
```

See detailed structure guidance in `docs/architecture/repository_structure.md`.

## How to Navigate This Repo
Start here based on your role:

1. **Architect / Reviewer**
   - Read `.agent/guides/` then `.agent/plans/master_plan.md`
2. **Environment / Core Simulation Developer**
   - Work in `src/hart/`, `src/environment/`, `src/simulation/`, `src/schemas/`
   - Prefer defining shared contracts in `src/hart/` before using them in runtime modules
3. **Agent Developer (Red/Blue/Adaptive)**
   - Work in `src/agents/`
4. **Observability & Evaluation Engineer**
   - Work in `src/logging/`, `src/metrics/`, `src/visualization/`
5. **Experimentation / Research Engineer**
   - Work in `src/experiments/`, `scenarios/`, `configs/`, `artifacts/`
6. **Validation Engineer**
   - Work in `tests/` and ensure seed-based reproducibility checks

## Running Tests

Use `pytest` from the repository root.

Assumption: your Python environment is already activated.

- Run full test suite:
   - `python -m pytest -q`
- Run all unit tests only:
   - `python -m pytest tests/unit -q`
- Run one specific test file:
   - `python -m pytest tests/unit/test_simulation_kernel.py -q`
- Run one specific test function:
   - `python -m pytest tests/unit/test_simulation_kernel.py::test_seed_reproducibility -q`

For reproducible baseline smoke execution:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase1_smoke.py`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_phase1_smoke.py`

## Run Phase 1 Baseline

From repository root:

1. Set up environment (once):
   - `python -m venv .venv`
   - PowerShell: `.venv\Scripts\Activate.ps1`
   - Bash/Zsh: `source .venv/bin/activate`
   - `python -m pip install -r requirements.txt`
2. Validate Phase 1 unit tests suite:
   - `python -m pytest tests/unit -q`
3. Run Phase 1 smoke path and generate artifacts:
   - PowerShell: `$env:PYTHONPATH='src'; python scripts/run_phase1_smoke.py`
   - Bash/Zsh: `PYTHONPATH=src python scripts/run_phase1_smoke.py`
4. Inspect outputs:
   - `artifacts/runs/<run_id>/run_metadata.json`
   - `artifacts/runs/<run_id>/timesteps.jsonl`


## Current Status

- **Phase 1 (Network Simulation Core): Completed**
   - Schema validation, graph initialization, transition primitives, legal actions, seeded simulation kernel, state diff utilities, and artifact logging scaffold are implemented.
   - Test framework migrated to `pytest`; unit suite passing.
- **Phase 2 (Rule-Based Agents): In progress**
   - Policy interface/registry, deterministic red/blue rule-based policies, explainable rationale payloads, and policy metrics snapshots are integrated into the simulation kernel.
- **Phase 3–5: Planned / Not started yet**
   - See `.agent/plans/` for phase-specific implementation definitions.



## Quick Setup for Collaborators
This section will be expanded with:
- environment prerequisites,
- dependency installation,
- canonical run/test commands,
- reproducibility workflow,
- contributor conventions.

Immediate baseline setup commands:
- Create virtual environment (from repo root):
   - `python -m venv .venv`
- Activate virtual environment:
   - PowerShell: `.venv\Scripts\Activate.ps1`
   - Bash/Zsh: `source .venv/bin/activate`
- `python -m pip install -r requirements.txt`
- `python -m pytest -q`


## Contributing Expectations
- Follow all constraints in `.agent/guides/`.
- Do not bypass phase plans without revision-log updates.
- Keep all behavior sandboxed and abstract.
- Ensure every change remains measurable, logged, and reproducible.
