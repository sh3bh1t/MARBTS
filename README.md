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
- `.agent/plans/phase_6_productization_delivery.md`

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
│  ├─ observability/
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
   - Work in `src/observability/`, `src/metrics/`, `src/visualization/`
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

For reproducible network core smoke execution:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_network_core_smoke.py`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_network_core_smoke.py`

For rule baseline smoke execution:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_rule_baseline_smoke.py`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_rule_baseline_smoke.py`

For multi-seed aggregate report generation:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_multi_seed_report.py --config configs/experiments/multi_seed_baseline.json`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_multi_seed_report.py --config configs/experiments/multi_seed_baseline.json`

For adaptive planning smoke execution (adaptive red vs rule-based blue):
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_adaptive_planning_smoke.py`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_adaptive_planning_smoke.py`

For adaptive-vs-rule experiment matrix report generation:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_policy_experiment_matrix.py --config configs/experiments/policy_experiment_matrix_baseline.json`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_policy_experiment_matrix.py --config configs/experiments/policy_experiment_matrix_baseline.json`

For batch matrix execution across multiple scenarios:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_policy_experiment_matrix.py --scenario-batch scenarios/baselines/rule_baseline.json,scenarios/library/containment_stress.json`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_policy_experiment_matrix.py --scenario-batch scenarios/baselines/rule_baseline.json,scenarios/library/containment_stress.json`

For comparative report packaging from two run directories:
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_comparative_report.py --left-run-dir artifacts/runs/<run_id_a> --right-run-dir artifacts/runs/<run_id_b>`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_comparative_report.py --left-run-dir artifacts/runs/<run_id_a> --right-run-dir artifacts/runs/<run_id_b>`
   - Outputs: `reports/comparative_report_<run_id_a>_vs_<run_id_b>.json`, matching `.md` summary, and SVG figures in `artifacts/figures/`.

For scenario catalog smoke execution :
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_scenario_catalog_smoke.py`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_scenario_catalog_smoke.py`

For decoy/bluff adaptive hook smoke execution :
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_deception_hooks_smoke.py`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_deception_hooks_smoke.py`

For stress-test suite execution :
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_stress_test_suite.py --config configs/experiments/stress_test_suite_baseline.json`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_stress_test_suite.py --config configs/experiments/stress_test_suite_baseline.json`

For ablation report package generation :
- PowerShell: `$env:PYTHONPATH='src'; python scripts/run_ablation_report.py --config configs/experiments/ablation_report_baseline.json`
- Bash/Zsh: `PYTHONPATH=src python scripts/run_ablation_report.py --config configs/experiments/ablation_report_baseline.json`
- Optional containerized profile: add `--containerized` to emit a container execution profile artifact.

For notebook asset smoke validation :
- `python scripts/run_notebook_smoke.py`

For notebook analysis workflows :
- See `notebooks/README.md` for curated replay/comparison, matrix, and ablation walkthrough notebooks.
- In notebooks, set `RUN_GENERATORS=True` to regenerate canonical artifacts in-place, or keep `False` to analyze existing outputs.

For packaged CLI execution :
- Install editable package:
   - `python -m pip install -e .`
- Show command surface:
   - `marbts --help`
- Run multi-seed report with presets:
   - `marbts-multi-seed-report --config configs/experiments/multi_seed_baseline.json`
- Run policy matrix with presets:
   - `marbts-policy-experiment-matrix --config configs/experiments/policy_experiment_matrix_baseline.json`
- Run stress suite with presets:
   - `marbts-stress-test-suite --config configs/experiments/stress_test_suite_baseline.json`
- Run ablation package with presets:
   - `marbts-ablation-report --config configs/experiments/ablation_report_baseline.json`
- Run container profile dispatcher:
   - `marbts-container-profile --spec multi_seed_baseline --dry-run`
   - `marbts container-profile --spec policy_matrix_baseline`

For Docker runtime execution :
- Build the project image:
   - `docker compose -f docker/docker-compose.yml build`
- Run multi-seed baseline:
   - `docker compose -f docker/docker-compose.yml --profile multi-seed run --rm multi-seed-report`
- Run policy matrix baseline:
   - `docker compose -f docker/docker-compose.yml --profile policy-matrix run --rm policy-experiment-matrix`
- Run stress suite baseline:
   - `docker compose -f docker/docker-compose.yml --profile stress-suite run --rm stress-test-suite`
- Run ablation report baseline:
   - `docker compose -f docker/docker-compose.yml --profile ablation-report run --rm ablation-report`
- Host-side compose profile runner (same canonical specs):
   - `python scripts/run_container_profile.py --spec multi_seed_baseline --dry-run`

Examples:
- PowerShell (custom seeds and horizon):
   - `$env:PYTHONPATH='src'; python scripts/run_multi_seed_report.py --seeds 20260329,20260332,20260333 --horizon 10`
- Bash/Zsh (custom scenario and output roots):
   - `PYTHONPATH=src python scripts/run_multi_seed_report.py --scenario scenarios/baselines/rule_baseline.json --runs-root artifacts/runs --metrics-root artifacts/metrics --reports-root artifacts/reports`
- PowerShell (scenario batch matrix execution):
   - `$env:PYTHONPATH='src'; python scripts/run_policy_experiment_matrix.py --scenario-batch scenarios/baselines/rule_baseline.json,scenarios/library/containment_stress.json`
- PowerShell (matrix with ablations):
   - `$env:PYTHONPATH='src'; python scripts/run_policy_experiment_matrix.py --seeds 20260423,20260424 --horizon 2`
- Bash/Zsh (matrix without ablations):
   - `PYTHONPATH=src python scripts/run_policy_experiment_matrix.py --skip-ablations`

## Run Network Core Baseline

From repository root:

1. Set up environment (once):
   - `python -m venv .venv`
   - PowerShell: `.venv\Scripts\Activate.ps1`
   - Bash/Zsh: `source .venv/bin/activate`
   - `python -m pip install -r requirements.txt`
2. Validate Phase 1 unit tests suite:
   - `python -m pytest tests/unit -q`
3. Run network core smoke path and generate artifacts:
   - PowerShell: `$env:PYTHONPATH='src'; python scripts/run_network_core_smoke.py`
   - Bash/Zsh: `PYTHONPATH=src python scripts/run_network_core_smoke.py`
4. Inspect outputs:
   - `artifacts/runs/<run_id>/run_metadata.json`
   - `artifacts/runs/<run_id>/timesteps.jsonl`


## Current Status

- **Network Simulation Core: Completed**
   - Schema validation, graph initialization, transition primitives, legal actions, seeded simulation kernel, state diff utilities, and artifact logging scaffold are implemented.
   - Test framework migrated to `pytest`; unit suite passing.
- **Rule-Based Agents: Completed**
   - Policy interface/registry, deterministic red/blue rule-based policies, explainable rationale payloads, policy metrics snapshots, baseline metrics artifacts, and multi-seed aggregate reporting are integrated and validated.
- **Adaptive Autonomy: Completed**
   - Increment 1 complete: adaptive planning policy scaffold, safety-filtered legal action selection, planning/value trace payloads, and adaptive planning smoke execution.
   - Increment 2 complete: adaptive-vs-rule matrix runner, ablation toggles (`no_planning`, `reduced_observability`), condition-level aggregates, and baseline-relative deltas.
   - Increment 3 complete: expanded adaptive-blue and mixed-observability conditions, summary ranking views, and optional scenario-batch matrix execution.
- **Observability & Visualization: Completed**
   - Increment 1 complete: shared observability contracts, schema validation, provenance capture, and structured run artifact envelopes.
   - Increment 2 complete: replay utilities and comparative report packaging.
   - Increment 3 complete: compromise-trend plots, defense-efficiency summaries, response-latency reports, and markdown/SVG comparative packaging.
- **Advanced Research Extensions: Completed**
   - Increment 1 complete: scenario taxonomy heuristics and semantic-versioned scenario registry with latest-version selection.
   - Increment 2 complete: decoy/bluff tactic primitives with adaptive-policy hooks, rationale payload events, and deception-enabled matrix condition variants.
   - Increment 3 complete: stress-test suite for scale/noise/observability robustness profiling with profile rankings and observability-penalty summaries.
   - Increment 4 complete: ablation orchestration/report templates, research artifact manifests, and optional containerized execution profiles.
- **Productization and Delivery: In Progress**
   - Increment 1 complete: packaged install path (`pyproject.toml`), `marbts` CLI entry point, preset loaders, and real config/seed bundles under `configs/`.
   - Increment 2 complete: concrete Docker assets (`docker/Dockerfile`, `docker/docker-compose.yml`), canonical container execution specs, and container profile dispatcher (`marbts container-profile`).
   - Increment 3 complete: curated notebook pack (`notebooks/*.ipynb` + `notebooks/README.md`) and notebook asset smoke validation (`scripts/run_notebook_smoke.py` + `tests/unit/test_notebook_assets.py`).
   - Increment 4 pending: release validation automation and readiness checklist.



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
- `python -m pip install -e .`
- `python -m pytest -q`


## Contributing Expectations
- Follow all constraints in `.agent/guides/`.
- Do not bypass phase plans without revision-log updates.
- Keep all behavior sandboxed and abstract.
- Ensure every change remains measurable, logged, and reproducible.
