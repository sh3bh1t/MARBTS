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

## Source of Truth and Governance
Authoritative planning and execution constraints are defined in:
- `copilot/guides/project_principles.md`
- `copilot/guides/execution_rules.md`
- `copilot/guides/testing_and_validation.md`

Implementation roadmap and phase plans are defined in:
- `copilot/plans/master_plan.md`
- `copilot/plans/phase_1_network_simulation.md`
- `copilot/plans/phase_2_agents_rule_based.md`
- `copilot/plans/phase_3_autonomy_llm_rl.md`
- `copilot/plans/phase_4_logging_visualization.md`
- `copilot/plans/phase_5_advanced_research.md`

## Repository Structure

```text
MARBTS/
├─ README.md
├─ copilot/
│  ├─ guides/
│  └─ plans/
├─ src/marbts/
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
   - Read `copilot/guides/` then `copilot/plans/master_plan.md`
2. **Environment / Core Simulation Developer**
   - Work in `src/marbts/environment/`, `src/marbts/simulation/`, `src/marbts/schemas/`
3. **Agent Developer (Red/Blue/Adaptive)**
   - Work in `src/marbts/agents/`
4. **Observability & Evaluation Engineer**
   - Work in `src/marbts/logging/`, `src/marbts/metrics/`, `src/marbts/visualization/`
5. **Experimentation / Research Engineer**
   - Work in `src/marbts/experiments/`, `scenarios/`, `configs/`, `artifacts/`
6. **Validation Engineer**
   - Work in `tests/` and ensure seed-based reproducibility checks



## Quick Setup for Collaborators
This section will be expanded with:
- environment prerequisites,
- dependency installation,
- canonical run/test commands,
- reproducibility workflow,
- contributor conventions.


## Contributing Expectations
- Follow all constraints in `copilot/guides/`.
- Do not bypass phase plans without revision-log updates.
- Keep all behavior sandboxed and abstract.
- Ensure every change remains measurable, logged, and reproducible.
