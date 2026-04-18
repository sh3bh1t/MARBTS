# Master Plan: Sandboxed Red vs Blue Autonomous Cyber Defense Simulation

Conforms to guide files in .agent/guides/

## 1) Problem Definition

### 1.1 Research Problem
Cyber defense strategy research requires controllable, repeatable, explainable environments where attacker-defender dynamics can be studied without real-world risk. Existing ad hoc simulations frequently lack strict data contracts, deterministic reproducibility, and sufficient observability for publication-quality empirical claims.

### 1.2 Objective
Design and implement a sandboxed, modular Red vs Blue simulation platform that supports:
- rigorous controlled experiments,
- transparent agent decision analysis,
- reproducible outcomes,
- comparative evaluation of rule-based and adaptive (LLM/RL) policies.

### 1.3 Non-Goals
- Real exploit code integration
- External network interaction
- Operational offensive tooling

All behavior remains abstract and synthetic.

## 2) System Architecture

### 2.1 High-Level Architecture
Core subsystems:
1. Scenario & Configuration Layer
2. Network Environment Engine (graph model)
3. Agent Policy Layer (Red/Blue interchangeable policies)
4. Turn-Based Simulation Orchestrator
5. Event Logging & Metrics Pipeline
6. Evaluation & Experiment Runner
7. Visualization & Analysis Layer

### 2.2 Component Responsibilities
- Scenario Loader: loads versioned scenario definitions, validates schema, and builds initial state.
- Environment Engine: maintains graph state, enforces transition rules, computes valid actions.
- Red Agent Interface: selects offensive abstract actions (scan, exploit, lateral movement, escalation).
- Blue Agent Interface: selects defensive abstract actions (patch, block, isolate, monitor).
- Orchestrator: executes timestep loop, resolves action outcomes, updates state, emits events.
- Logger: writes immutable structured event stream and periodic state snapshots.
- Metrics Engine: computes online and post-hoc metrics.
- Experiment Runner: executes seeded batches, baseline comparisons, and ablations.

### 2.3 Modularity Contract
Every component is replaceable behind stable interfaces:
- environment adapter
- agent policy adapter
- outcome model adapter
- logging backend adapter

## 3) Data Model Design

### 3.1 Primary Entities
- Node
- Edge
- Vulnerability
- Service
- SecurityControl
- AgentActionIntent
- ActionOutcome
- TimestepState
- SimulationRunMetadata
- MetricSnapshot

### 3.2 Node Schema (Conceptual)
- node_id: string
- node_type: enum {server, database, iot, endpoint}
- services: list[service_id]
- vulnerabilities: list[vuln_id]
- security_level: int (bounded scale)
- compromised_state: enum {none, user, privileged}
- detection_state: enum {undetected, suspected, confirmed}
- isolation_state: bool

### 3.3 Action Contract
Agent action object must include:
- action_id
- actor (red|blue)
- action_type
- target(s)
- rationale
- predicted_effect
- confidence_or_utility
- timestamp/timestep

### 3.4 Logging Contract
Per timestep event requirements:
- pre_state_ref
- red_action_intent + rationale
- blue_action_intent + rationale
- action_resolution_outcomes
- post_state_diff
- metric_delta
- reproducibility metadata (seed, scenario_id, config_hash, commit_hash)

## 4) Agent Design Philosophy

### 4.1 Red Agent
Behavioral chain:
1. Scan
2. Exploit
3. Lateral movement
4. Privilege escalation

Policy requirements:
- bounded legal action space by environment constraints
- explicit rationale for every action
- uncertainty-aware selection (scores/utilities)

### 4.2 Blue Agent
Behavioral chain:
1. Monitor
2. Patch
3. Block
4. Isolate

Policy requirements:
- balance immediate containment vs long-term resilience
- preserve service continuity constraints where modeled
- provide explainable defense rationale

### 4.3 Policy Evolution Path
- Phase 2: deterministic rule-based policies
- Phase 3: adaptive policies, beginning with deterministic bounded planning and extending to LLM reasoning and/or RL
- Strict compatibility with common policy interface to support baseline comparisons

## 5) Simulation Loop Design

### 5.1 Turn Semantics
Per timestep t:
1. Capture pre-state snapshot reference
2. Red chooses action
3. Apply Red action and resolve probabilistic/deterministic effects
4. Blue observes updated partial/full state
5. Blue chooses response action
6. Apply Blue action
7. Compute post-state diff
8. Emit structured logs + metrics snapshot
9. Advance timestep

### 5.2 Determinism and Randomness
- Seeded PRNG controls stochastic resolution.
- Deterministic mode available for unit/integration tests.
- Run metadata records all determinism controls.

### 5.3 Termination Conditions
- Max timestep horizon reached
- Critical compromise threshold reached
- Defensive stabilization criterion reached
- Scenario-defined terminal state reached

## 6) Phase Roadmap

### Phase 1: Network Simulation Core
- Build graph-based environment using networkx
- Implement state model, transition rules, legal action generation
- Add seedable simulation kernel skeleton

### Phase 2: Rule-Based Agents
- Implement deterministic Red/Blue policy baselines
- Integrate policy interfaces with orchestrator
- Validate predictable tactical dynamics

### Phase 3: Adaptive Autonomy (LLM/RL)
- Add adaptive policies behind same interface, beginning with deterministic bounded-planning baselines and extending to LLM-reasoning or RL policies
- Add multi-step planning and utility shaping
- Compare against rule-based baselines

### Phase 4: Logging & Visualization
- Complete structured event pipeline and metrics dashboards
- Build trajectory replay and explainability views
- Validate logging completeness and schema conformance

### Phase 5: Advanced Research Extensions
- Decoy/bluff mechanisms
- Scenario library expansion
- Optional containerized simulation execution
- Robust ablations and stress experiments

## 7) Evaluation Metrics

### 7.1 Security Outcomes
- nodes_compromised_count
- time_to_first_compromise
- time_to_critical_compromise
- privilege_escalation_events

### 7.2 Defense Performance
- mean_time_to_detect
- mean_time_to_contain
- patch_effectiveness_rate
- isolation_false_positive_rate (if observability supports)

### 7.3 System Quality
- log_completeness_ratio
- schema_validation_pass_rate
- reproducibility_match_rate (same seed reruns)
- simulation_step_latency

### 7.4 Comparative Metrics
- rule_based_vs_adaptive delta on compromise prevention
- action efficiency (impact per action)
- resilience under scenario perturbation

## 8) Research-Paper Framing

### 8.1 Hypotheses
H1: Adaptive (LLM/RL) defenders reduce compromise progression versus rule-based defenders under equal scenario constraints.

H2: Explainability-constrained action selection (rationale + confidence logging) improves diagnosis of failure modes without materially degrading defensive performance.

H3: Decoy/bluff-enabled strategies improve blue-team containment efficiency in high-lateral-mobility topologies.

### 8.2 Experimental Design
- Controlled factorial experiments across:
  - topology complexity
  - vulnerability density
  - defender policy class
  - attacker aggressiveness
- Multiple seeds per condition
- Fixed scenario catalog with version pinning

### 8.3 Baselines
- Static rule-based Red + static rule-based Blue
- Rule-based Red + adaptive Blue
- Adaptive Red + rule-based Blue
- Adaptive Red + adaptive Blue

### 8.4 Reporting Metrics
Primary:
- nodes compromised
- time to compromise
- defense efficiency

Secondary:
- action explainability quality proxies
- stability/variance across seeds

### 8.5 Reproducibility Requirements
- Publish scenario definitions and schema versions
- Publish fixed seed sets
- Publish run metadata and config hashes
- Publish comparison scripts and metric computation definitions

## 9) Risks and Tradeoffs

### 9.1 Key Risks
- Overfitting agent policies to narrow scenario patterns
- Non-deterministic adaptive models reducing reproducibility
- Excessive logging overhead affecting run performance
- Explainability payload bloat reducing throughput

### 9.2 Tradeoff Decisions
- Prefer strict schemas over rapid prototyping flexibility
- Prefer deterministic defaults over maximum realism
- Prefer modular interfaces over tightly coupled optimized code in early phases
- Prefer explicit failure over silent coercion in data ingestion

## 10) Plan Revision Log

- 2026-04-18: Sequenced Phase 3 execution to begin with deterministic bounded-planning adaptive baselines before optional LLM/RL backends, preserving sandbox safety and reproducibility requirements.
- 2026-04-18: Recorded observability/provenance implementation under `src/simulation/*` and reporting under `src/visualization/*` to avoid collisions with Python's standard-library `logging` package namespace.
- 2026-04-18: Added an OpenAI Responses API-backed adaptive policy path using structured outputs with legal-action validation and guarded fallback to sandbox-safe local policies.
- 2026-04-18: Added a unified Phase 3 experiment matrix covering planner and OpenAI-backed policies plus `no_planning` and `reduced_observability` ablations behind shared adaptive configuration flags.

### 9.3 Mitigations
- Scenario diversity and holdout sets
- Fixed seed test battery and regression suites
- Configurable logging verbosity with mandatory minimum fields
- Periodic profiling and event compaction strategies

## 10) Milestone Checkpoints

### M1: Core Environment Ready (Phase 1)
- Graph engine operational
- State transitions validated
- Seed control operational

### M2: Baseline Agents Ready (Phase 2)
- Rule-based red/blue policies integrated
- Deterministic baseline scenarios pass acceptance

### M3: Adaptive Policies Integrated (Phase 3)
- LLM/RL policy adapter integrated
- Comparative experiments runnable

### M4: Observability Complete (Phase 4)
- Required event fields present
- Replay and metric dashboards functioning

### M5: Research Package Complete (Phase 5)
- Ablation studies complete
- Reproducibility package assembled
- Paper-ready experiment artifacts generated

## 10.1 Current Phase Status

- Phase 1: Completed (core implementation + pytest validation + smoke hardening)
- Phase 2: Not started
- Phase 3: Not started
- Phase 4: Not started
- Phase 5: Not started

## 11) Governance and Plan Maintenance

### 11.1 Mandatory Alignment Statement
Before any implementation step: "This step aligns with the master plan and guide constraints."

### 11.2 Validation Gate Statement
After each major feature or phase: "Validation complete for this step."

### 11.3 Plan Revision Log
- 2026-03-28: Initial master plan created from project directives and guide constraints.
- 2026-03-28: Added canonical repository scaffolding and directory governance alignment (src/tests/scenarios/configs/docs/artifacts/docker).
- 2026-03-28: Repository source layout flattened from `src/marbts/*` to `src/*`; imports/docs/plan references updated for compatibility.
- 2026-03-28: Testing framework standardized to pytest for contributor scalability and simpler assertion patterns.
- 2026-03-28: Added Phase 1 closure hardening assets (smoke runner and closure checklist/report path).
- 2026-03-28: Updated project docs with explicit collaborator test execution instructions and phase status tracking.
- 2026-03-29: Introduced centralized `src/hart/` type system (enums/models) and refactored Phase 1 modules to consume shared contracts.
