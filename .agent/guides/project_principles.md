# Project Principles

## Authority and Scope
This document is authoritative for all planning and implementation work in this repository.
All subordinate plans and execution steps must conform to this file, `.agent/guides/execution_rules.md`, and `.agent/guides/testing_and_validation.md`.

## Engineering Persona
Work must reflect the operating standard of a senior AI + cybersecurity engineer with deep experience in autonomous agents, LLM systems, RL pipelines, distributed systems, and production reliability.

Design posture:
- FAANG-grade system design discipline
- Research-grade methodological rigor
- Explicit tradeoff analysis over convenience
- Safety-by-design for cyber simulation constraints

## System Mission
Build a sandboxed Red vs Blue autonomous cyber defense simulation framework that is:
- Modular
- Explainable
- Reproducible
- Suitable for peer-reviewable research artifacts

## Non-Negotiable Constraints
- Sandbox-only operation; no real-world exploitation tooling or unsafe operational behaviors.
- Abstract simulation actions only; no actionable offensive instructions.
- No hidden logic: all decisions must be explainable and logged.
- No silent assumptions: uncertainty requires clarification before implementation.
- Deterministic behavior where feasible via controlled random seeds.

## Architecture Principles
- Modular composition: environment, agents, policies, simulation engine, and analytics are independently replaceable.
- Strict interfaces and data contracts using explicit schemas.
- Event-sourced observability: state transitions and actions are persisted as structured events.
- Reproducibility-first runtime: same seed + scenario + configs must produce equivalent trajectories.
- Experiment-driven design: all components must map to measurable hypotheses.

## Build-vs-Buy Principle
- Default to a library-first approach across all domains when mature packages provide clear gains in correctness, maintainability, safety, testability, or implementation speed.
- Keep third-party usage behind stable module boundaries so dependencies remain replaceable.
- Use custom implementations only when constraints or risks make external dependencies unsuitable, and document that rationale in the corresponding plan/doc update.

## Data and Contract Principles
- Use strict schema definitions for scenario config, node state, action intents, action outcomes, and metrics snapshots.
- Version all schemas and scenario definitions.
- Reject malformed inputs explicitly; never coerce silently.
- Include provenance metadata for each run (seed, code version, scenario id, timestamp, config hash).

## Explainability Requirements
Every agent action must produce:
- decision rationale
- selected action
- expected objective impact
- observed outcome
- confidence or utility estimate (if applicable)

## Security and Safety Guardrails
- Do not integrate real exploit frameworks.
- Do not include live scanning against external targets.
- Keep all behavior in synthetic network state space.
- Restrict interactions to local simulation abstractions.

## Research Integrity Requirements
Each implemented capability must be:
- measurable
- logged
- reproducible

If any component fails one of these checks, redesign before acceptance.
