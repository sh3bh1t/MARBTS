# Repository Structure

Conforms to guide files in copilot/guides/

## Purpose
This document defines the canonical directory layout for MARBTS. It is designed for modularity, explainability, reproducibility, and research-grade experiment management.

## Top-Level Layout

- `copilot/` — Authoritative guides and phased implementation plans.
- `idea-core/` — Project definition artifacts.
- `src/marbts/` — Main Python package.
- `tests/` — Unit/integration/simulation/reproducibility/regression test suites.
- `scenarios/` — Versioned scenario schemas and libraries.
- `configs/` — Base runtime configs, experiment configs, and seed sets.
- `scripts/` — Reproducible CLI entry scripts for simulation and experiments.
- `docs/` — Architecture, operations, and research documentation.
- `notebooks/` — Exploratory analysis notebooks (non-authoritative).
- `artifacts/` — Generated run outputs, metrics, figures, and reports.
- `docker/` — Optional containerized execution assets.

## Source Package Layout (`src/marbts/`)

- `core/` — Shared domain primitives, constants, and base interfaces.
- `environment/` — Graph network model, state transitions, legal action generation.
- `agents/interfaces/` — Stable policy interface contracts.
- `agents/red/` — Rule-based and adaptive Red policy implementations.
- `agents/blue/` — Rule-based and adaptive Blue policy implementations.
- `agents/adaptive/` — Common adaptive policy components (LLM/RL adapters/planners).
- `simulation/` — Turn-based orchestrator and timestep lifecycle.
- `schemas/` — Strict schema definitions and validators.
- `logging/` — Structured event pipeline and run provenance.
- `metrics/` — Online and post-hoc metric computation.
- `experiments/` — Experiment matrix, baselines, and ablation orchestration.
- `visualization/` — Replay and reporting visual outputs.
- `utils/` — Utility modules with minimal shared helpers.

## Scalability Rules

1. Keep interfaces stable and implementation modules replaceable.
2. Preserve clear boundaries between environment, policy, and orchestration.
3. Store generated data only under `artifacts/`.
4. Store static scenario/config inputs only under `scenarios/` and `configs/`.
5. Keep research scripts deterministic by explicitly passing seed/config IDs.

## Ownership Mapping by Phase

- Phase 1: `environment/`, `schemas/`, `simulation/`
- Phase 2: `agents/interfaces/`, `agents/red/`, `agents/blue/`
- Phase 3: `agents/adaptive/`, `experiments/`
- Phase 4: `logging/`, `metrics/`, `visualization/`
- Phase 5: `scenarios/library/`, `experiments/`, `docker/`, `docs/research/`
