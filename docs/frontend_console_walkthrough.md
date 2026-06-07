# MARBTS Frontend Walkthrough

This frontend is a local control console for the MARBTS simulation platform. It does not replace the Python project; it exposes the existing project capabilities in one place so someone can inspect scenarios, run simulations, replay artifacts, generate reports, and check delivery readiness.

## High-Level Story

Use this framing when explaining the system:

MARBTS models a sandboxed Red vs Blue cyber-defense environment. A scenario defines a synthetic network. Red and Blue policies choose legal actions on that network. The simulator applies state transitions, writes every decision as an artifact, and then reports aggregate behavior across seeds, scenarios, and policy variants.

The frontend follows that same order:

1. Choose and inspect the scenario.
2. Run a seeded simulation with selected Red and Blue policies.
3. Replay the recorded artifacts to explain each action.
4. Generate reports to evaluate stability and compare policies.
5. Use operations checks to show packaging and reproducibility readiness.

## Header And Navigation

The top header shows the project root and live counts for scenarios, runs, metrics, and reports. Explain this as the frontend's quick status view of the local repository.

The left navigation separates the workflow into five areas:

- Scenarios: what network world are we simulating?
- Run: what happens in one Red vs Blue execution?
- Replay: can we audit and reproduce the run?
- Reports: what do repeated experiments show?
- Ops: is the project ready to package and run consistently?

## Scenario Catalog

This page shows the scenario library. Each row is a JSON scenario loaded through the project's schema code.

Explain the main pieces:

- Scenario table: lists scenario ID, source group, node count, edge count, and taxonomy tags.
- Tags: summarize topology complexity, vulnerability density, and defense posture.
- Metric cards: show counts such as nodes, edges, vulnerabilities, average security level, isolated nodes, and initial compromised nodes.
- Topology graph: shows how nodes are connected, which matters because lateral movement and blocking depend on graph structure.
- Scenario validator: lets you load or paste scenario JSON and validate it before simulation.

Suggested talk track:

“The scenario is the source of truth for the environment. Before we talk about agents or metrics, we need to know what network they are acting on. The catalog tells us the network size and risk profile, and the validator makes sure a scenario is structurally valid.”

## Simulation Run

This page executes one simulation. You choose the scenario, seed, horizon, and Red/Blue policies.

Explain the controls:

- Scenario: selects the network to simulate.
- Seed: controls deterministic replay.
- Horizon: number of turns to execute.
- Red Policy and Blue Policy: choose rule-based or adaptive behavior.
- Planning Horizon: how far an adaptive policy projects action value.
- Exploration: how much adaptive policies reward less-used action types.
- Decision Noise: deterministic seed-based variation for adaptive choices.
- Reduced Observability: limits how much compromise pressure the adaptive policy can observe.
- Decoy and Bluff: enable deception-related adaptive hooks.

Explain the output:

- Run Summary: high-level metrics for the completed run.
- Turn slider: moves through graph snapshots after each turn.
- Graph: shows compromised, isolated, and clean node states over time.
- Action Timeline: shows Red action, Blue response, targets, rationale, and compromise delta.

Suggested talk track:

“This is one controlled execution. Red chooses an offensive action, Blue responds defensively, and the environment updates the graph. Because the run is seeded, we can replay the same behavior and compare it fairly against other policies.”

## Replay Artifacts

This page reads artifacts that have already been written to `artifacts/runs`.

Explain the main pieces:

- Run table: lists run IDs and basic configuration.
- Replay summary: shows seed, horizon, final compromised nodes, containment actions, and first containment timestep.
- Integrity status: compares the replayed action-sequence hash with the stored policy metrics hash.
- Replay timeline: reconstructs each timestep from JSONL event logs.

Suggested talk track:

“The simulator is explainable because it stores every timestep. We are not just trusting a final score; we can inspect exactly which actions were chosen, what changed, and whether the replayed sequence matches the stored metrics.”

## Reports

This page generates and views higher-level research artifacts.

Explain each report generator:

- Multi Seed: runs the same scenario across multiple seeds and aggregates final compromise, containment timing, and deterministic consistency.
- Policy Matrix: compares rule and adaptive Red/Blue pairings, optionally including ablations.
- Stress Suite: runs predefined stress profiles across larger or noisier scenario sets.
- Ablation Package: converts policy matrix results into publication-style tables and optional container execution metadata.
- Comparative Report: compares two run directories and generates metric deltas plus report artifacts.

Explain the artifact viewer:

The artifact table lists generated JSON and Markdown reports. Selecting a row opens the artifact inline, so the demo can move from buttons to actual generated evidence.

Suggested talk track:

“One simulation is useful for explanation, but reports are what make the project research-grade. They show whether behavior is stable across seeds, how policies compare, and what changes when planning or observability is ablated.”

## Operations

This page is for delivery and reproducibility checks.

Explain the two components:

- Release Validation: runs pass/fail gates for packaging, presets, seed bundles, Docker assets, notebooks, scripts, tests, stub removal, and README currency.
- Container Profile: resolves the Docker Compose command for canonical experiment profiles. Dry run shows the command without executing it.

Suggested talk track:

“This page is about proving the project can be handed off. The release gates check expected assets, and the container profile shows exactly how the canonical experiments would run in Docker.”

## Suggested Demo Order

1. Start at Scenarios and select `rule-baseline`.
2. Show the topology graph and explain the nodes, edges, vulnerabilities, and security levels.
3. Load the selected scenario JSON into the validator and validate it.
4. Move to Run and execute a short rule-vs-rule simulation.
5. Use the turn slider and timeline to explain how Red and Blue decisions changed the network.
6. Move to Replay and select the new run to show artifact-level auditability.
7. Move to Reports and generate a small multi-seed report.
8. Open the generated artifact in the viewer.
9. Finish in Operations by running release validation or resolving a container profile.

## One-Minute Explanation

“This frontend is the control console for MARBTS. We start by choosing a synthetic network scenario. Then we run seeded Red vs Blue simulations using rule-based or adaptive policies. Every timestep is recorded with action rationale, state changes, metrics, and provenance. The replay page lets us audit that record, while the reports page aggregates multiple runs for comparison and reproducibility. Finally, the operations page checks whether the project is packaged and runnable through the expected scripts and container profiles.”

