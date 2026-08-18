# MARBTS Simulation Reference Guide

Everything you need to run, read, and understand the live simulation and all CLI tools.

---

## 1. Running `watch_sim.py` — Quick Reference

```bash
# Default: animated, 5 seconds per turn, random seed, enterprise_medium scenario
python watch_sim.py

# Replay a specific run (deterministic)
python watch_sim.py --seed 200         # Red Advantage   — 13/20 nodes compromised
python watch_sim.py --seed 195         # Blue Holds      —  4/20 nodes compromised
python watch_sim.py --seed 42          # Red Advantage   — ~12/20 nodes compromised
python watch_sim.py --seed 100         # Blue Advantage  —  7/20 nodes compromised

# Speed control
python watch_sim.py --delay 2          # 2 seconds per turn
python watch_sim.py --delay 10         # 10 seconds per turn (very deliberate)
python watch_sim.py --fast             # instant — no delays at all

# Game length
python watch_sim.py --turns 30         # 30 turns (default: 20)
python watch_sim.py --turns 50         # long game — advantages compound
python watch_sim.py --turns 10         # short game — early chaos

# Scenarios
python watch_sim.py --scenario enterprise_medium    # 20 nodes (default)
python watch_sim.py --scenario scale_chain_6        # 6-node linear chain
python watch_sim.py --scenario containment_stress   # 3-node, pre-breached
python watch_sim.py --scenario rule_baseline        # 4-node minimal baseline

# Policy mode
python watch_sim.py --policy adaptive   # AdaptivePlanningPolicy, seed-noisy (default)
python watch_sim.py --policy rule       # Deterministic rule-based policies

# Disable probabilistic exploit resistance (all exploits succeed)
python watch_sim.py --no-resistance

# Combine flags
python watch_sim.py --seed 200 --turns 30 --delay 3
python watch_sim.py --fast --turns 50 --seed 42

# Output
# Every run is automatically saved to:  output/runs/run_YYYYMMDD_HHMMSS_seed<N>.txt
# The path is printed in the terminal at the end of each run.
# Structured JSON artifacts are saved to:  artifacts/runs/<run_id>/
```

---

## 2. What Each Turn Shows — Field-by-Field Explanation

Each turn is displayed like this:

```
──────────────────────────────────────────────────────────────────────
  TURN 3 / 25

  ▶ RED   EXPLOIT          → 03-mail
       Rationale  : selected exploit using bounded adaptive planning
       Expected   : increase probability of initial or expanded compromise
       Plan       : horizon=3  cumulative=22.256  [t+0:8.25  t+1:7.39  t+2:6.61]
       Confidence : 0.55   utility=30.24
       Outcome    : ✓ CHANGED  — compromise level increased by one

  ▶ BLUE  PATCH            → 09-bastion
       Rationale  : selected patch using bounded adaptive planning
       Expected   : reduce vulnerable surface and compromise persistence
       Plan       : horizon=3  cumulative=22.858  [t+0:8.95  t+1:7.61  t+2:6.30]
       Confidence : 0.54   utility=29.72
       Outcome    : ✓ CHANGED  — security level +1; removed one vulnerability

  Δ State changes this turn:
    03-mail: compromised_state: none → user
    09-bastion: vulnerabilities: ['cve-sim-520'] → [] | security_level: 9 → 10

  Score: [██░░░░░░░░░░░░░░░░░░] 2/20 nodes compromised  ↑ +1 RED gains

  ──────────────────────────────────────────────────────────────────
  NETWORK STATE  turn 3/25
  ...
```

### Turn header
| Element | Meaning |
|---|---|
| `TURN 3 / 25` | Current turn number and total turns in this game |

### Red / Blue action block
| Field | Meaning |
|---|---|
| `▶ RED EXPLOIT → 03-mail` | Actor (Red), action type chosen, and the target node(s) |
| `Rationale` | One-line policy summary of WHY this action was selected |
| `Expected` | Predicted effect on the network if the action succeeds |
| `Plan` | 3-step lookahead from the AdaptivePlanningPolicy: `horizon=N` is how many future steps were projected; `cumulative=X.XXX` is the total discounted utility over those steps; `[t+0:X  t+1:X  t+2:X]` is the discounted utility at each future step |
| `Confidence` | How confident the agent is in this decision (0.35–1.0 scale derived from utility) |
| `utility=X.XX` | Raw total score that caused this action to be selected (planning utility + exploration bonus + target affinity + decision noise) |
| `✓ CHANGED` | The action succeeded and changed game state |
| `✗ blocked/no-op` | The action was attempted but had no effect — either the node resisted the exploit or the edge/state was already at the boundary |
| Outcome reason | Detail of what specifically happened: e.g. `exploit resisted by security controls (sec_level=6, threshold=0.50)` means Red rolled unlucky against a 50% success probability |

### State changes (Δ)
| Field | Meaning |
|---|---|
| `compromised_state: none → user` | Node was clean, now has user-level compromise (Red foothold established) |
| `compromised_state: user → privileged` | Existing user foothold escalated to full root/admin privileges — costs Blue 2 patches to fully recover |
| `compromised_state: privileged → user` | Blue patched a privileged node back down one level |
| `compromised_state: user → none` | Blue fully recovered a user-compromised node (clean again) |
| `security_level: N → N+1` | Blue patched this node, hardening it — higher security means future exploits have lower success probability |
| `vulnerabilities: ['cve-sim-XXX'] → []` | Blue removed the known vulnerability — node can still be exploited by ESCALATE but not by EXPLOIT (which requires a listed vulnerability) |
| `isolation_state: false → true` | Blue isolated this node — all edges severed, no lateral movement in/out possible, Red exploits auto-blocked |
| `edge severed: A ↔ B` | Blue used BLOCK to remove the network path between two nodes |

### Score bar
```
Score: [█████████████░░░░░░░] 13/20 nodes compromised  ↑ +1 RED gains
```
| Element | Meaning |
|---|---|
| `[█ filled ░ empty]` | Visual compromise ratio — filled blocks are compromised nodes |
| `13/20` | Current compromised node count / total nodes |
| `↑ +N RED gains` | Red compromised N more nodes this turn compared to last turn |
| `↓ -N BLUE recovers` | Blue recovered N nodes this turn (patching worked) |
| `— no change` | Compromise count did not change this turn |

### Network State view (shown every 5 turns and after state changes)
```
  Perimeter  (sec 1-3)
    01-ext    ◼ PRIV    suspected   live     sec=1
    03-mail   ▪ user    undetected  live     sec=3
    03-proxy  ◻ clean   undetected  ISOLATED sec=4
```
| Symbol / Field | Meaning |
|---|---|
| `◼ PRIV` (red) | Node is compromised at **privileged** level — attacker has root/admin. Costs Blue 2 patches to clear |
| `▪ user` (red) | Node is compromised at **user** level — attacker has initial foothold |
| `◻ clean` (green) | Node is not compromised |
| `suspected` / `detected` | Blue has flagged this node as suspicious (detection_state) |
| `undetected` | Blue has not flagged this node |
| `ISOLATED` (red) | Node has been isolated by Blue — all network edges severed, no traffic in or out |
| `live` | Node is connected to the network |
| `sec=N` | Current security level (1–10). Higher = harder to exploit. At sec=10, exploit success probability is 25% (floor). Blue's PATCH raises this by 1 per application |
| **Perimeter tier** | Nodes `01-ext` through `03-proxy` — lowest security (sec 1-3), Red targets these first |
| **Internal tier** | Nodes `04-*` through `05-*` — mid-tier (sec 3-5), Red spreads here via lateral movement |
| **Core tier** | Nodes `06-*` through `09-bastion` — highest security (sec 6-9), databases + auth + bastion, Blue fortifies these |

### Exploit resistance line
When Red fails an exploit, you'll see:
```
Outcome    : ✗ blocked/no-op  — exploit resisted by security controls (sec_level=6, threshold=0.50)
```
`threshold=0.50` means there was a 50% chance of success. The formula is `max(0.25, 1.0 - (sec_level - 1) / 10.0)`. At sec=1: 100%. At sec=6: 50%. At sec=10: 25%.

---

## 3. Final Verdict — Outcome Tiers

| Verdict | Condition | Meaning |
|---|---|---|
| **BLUE WINS** | 0/20 compromised | Red made no progress — perfect defence |
| **BLUE HOLDS** | < 6/20 (< 30%) | Breach contained at the perimeter, core fully intact |
| **BLUE ADVANTAGE** | 6–8/20 (30–40%) | Red took some perimeter nodes, Blue held everything else |
| **CONTESTED** | 9–11/20 (45–55%) | Battle genuinely undecided; neither side dominates |
| **RED ADVANTAGE** | 12–13/20 (60–65%) | Red breached perimeter + internal; crown jewels holding by a thread |
| **RED WINS** | ≥ 14/20 (≥ 70%) | Critical mass — Red has majority control of the network |

Observed outcome distribution across 500 seeds (25 turns):
- ~2% BLUE HOLDS (seeds like 195)
- ~42% BLUE ADVANTAGE (seeds like 100, 300, 400)
- ~46% CONTESTED (seeds like 99, 1000, 1234)
- ~8% RED ADVANTAGE (seeds like 42, 200)
- ~0% RED WINS (extremely rare, requires lucky Red + unlucky Blue)

---

## 4. Saved Output Files

Every `python watch_sim.py` run saves two sets of files automatically:

### `output/runs/` — Human-readable plain-text log
```
output/runs/run_20260425_083000_seed200.txt
```
- Plain text with ANSI codes stripped — readable in any editor
- Contains the complete terminal session: banner, topology, every turn, final verdict
- Filename encodes: date, time, and the seed used
- Created by the `_TeeOutput` class that mirrors stdout to disk

### `artifacts/runs/<run_id>/` — Structured JSON artifacts
```
artifacts/runs/e0e3ced44f802528/
  timesteps.jsonl      ← one JSON line per turn: actions, rationale, state diff, metrics
  run_metadata.json    ← seed, scenario_id, horizon, timestamp, commit provenance
  policy_metrics.json  ← per-agent action type counts (how often each action was used)
```

---

## 5. All MARBTS CLI Commands

Install (if not already installed):
```bash
pip install -e .
```

### `marbts` — Main dispatcher

```bash
marbts --help
# MARBTS packaged CLI. Use subcommands for experiment workflows.
# Subcommands: multi-seed-report, policy-experiment-matrix,
#              stress-test-suite, ablation-report,
#              container-profile, release-validation
```

All subcommands are also available as standalone executables (see below).

---

### `marbts-multi-seed-report`

**What it does:** Runs the simulation across multiple seeds and produces an aggregate statistical report. Useful for checking whether outcomes are consistent (high deterministic_consistency_ratio) or vary significantly across seeds.

**Sample run:**
```bash
marbts-multi-seed-report \
  --scenario scenarios/library/scale_chain_6.json \
  --seeds 42,100 \
  --horizon 5
```

**Sample output:**
```
MULTI_SEED_REPORT_OK
timestamp_utc=2026-04-25T03:21:33.801735+00:00
scenario_id=scale-chain-6
seed_count=2
horizon=5
final_compromised_mean=1.0
deterministic_consistency_ratio=1.0
report_file=artifacts/reports/multi_seed_report_scale-chain-6.json
```

**Key output fields:**
| Field | Meaning |
|---|---|
| `final_compromised_mean` | Average compromised nodes across all seeds |
| `deterministic_consistency_ratio` | 1.0 = all seeds produced identical outcomes (rule-based policies); < 1.0 = outcomes varied |
| `report_file` | Path to full JSON report with per-seed breakdown |

**All flags:**
```
--config CONFIG           Path to experiment preset JSON (overrides individual flags)
--scenario SCENARIO       Path to scenario JSON file
--seeds SEEDS             Comma-separated integer seeds  e.g. 42,100,200
--horizon HORIZON         Turns per simulation run
--runs-root RUNS_ROOT     Where to write run artifacts (default: artifacts/runs)
--metrics-root            Where to write metrics artifacts
--reports-root            Where to write the aggregate report
```

---

### `marbts-policy-experiment-matrix`

**What it does:** Runs a full 2×2 policy experiment matrix (Adaptive Red vs Rule Blue, Rule Red vs Adaptive Blue, Both Adaptive, Both Rule) across seeds and scenarios, then reports comparative metrics. Core research command for evaluating policy effectiveness.

**Sample run:**
```bash
marbts-policy-experiment-matrix \
  --scenario scenarios/library/scale_chain_6.json \
  --seeds 42,100 \
  --horizon 5 \
  --skip-ablations
```

**Sample output:**
```
POLICY_EXPERIMENT_MATRIX_OK
timestamp_utc=2026-04-25T03:21:37.540498+00:00
scenario_id=scale-chain-6
seed_count=2
horizon=5
condition_count=4
include_ablations=False
report_file=artifacts/reports/policy_experiment_matrix_scale-chain-6.json
```

**Key output fields:**
| Field | Meaning |
|---|---|
| `condition_count` | Number of policy combinations tested (4 for 2×2 matrix) |
| `include_ablations` | Whether reduced-observability / decoy-bluff variants were included |
| `report_file` | JSON with per-condition metrics: compromise rate, action counts, efficiency |

**All flags:**
```
--config CONFIG                     Experiment preset JSON (overrides flags)
--scenario SCENARIO                 Single scenario JSON file
--scenario-batch SCENARIO_BATCH     Comma-separated list of scenario files (batch mode)
--seeds SEEDS                       Comma-separated seeds
--horizon HORIZON                   Turns per run
--skip-ablations                    Only run the 4 base conditions (no variant ablations)
--runs-root / --metrics-root / --reports-root   Output directories
```

---

### `marbts-stress-test-suite`

**What it does:** Runs a multi-profile stress test covering scale scenarios (large networks) and noise/observability constraints (reduced observability, reduced-noise ablations). Measures policy robustness under degraded conditions.

**Sample run:**
```bash
marbts-stress-test-suite --seeds 42 --horizon 5
```

**Sample output:**
```
STRESS_TEST_SUITE_OK
timestamp_utc=2026-04-25T03:21:50.987660+00:00
profile_count=2
profiles=scale_scenarios,noise_observability_constraints
report_file=artifacts/reports/stress_test_suite_report.json
```

**Key output fields:**
| Field | Meaning |
|---|---|
| `profile_count` | Number of stress profiles run (2: scale + noise/observability) |
| `profiles` | `scale_scenarios` = large/complex topologies; `noise_observability_constraints` = degraded Blue observability |
| `report_file` | Per-profile ranked robustness results |

**All flags:**
```
--config CONFIG         Experiment preset JSON
--seeds SEEDS           Comma-separated seeds
--horizon HORIZON       Turns per stress run
--runs-root / --metrics-root / --reports-root   Output directories
```

---

### `marbts-ablation-report`

**What it does:** Generates a research-grade ablation report package. Runs the policy matrix, generates comparison tables (with/without planning, with/without observability), and produces a JSON template ready for paper writing. Optionally generates a container execution profile for reproducible runs.

**Sample run:**
```bash
marbts-ablation-report \
  --scenario scenarios/library/scale_chain_6.json \
  --seeds 42 \
  --horizon 5 \
  --skip-ablations
```

**Sample output:**
```
ABLATION_REPORT_PACKAGE_OK
timestamp_utc=2026-04-25T03:21:51.558205+00:00
scenario_id=scale-chain-6
seed_count=1
horizon=5
condition_count=4
table_count=2
containerized=False
matrix_report_file=artifacts/reports/policy_experiment_matrix_scale-chain-6.json
template_file=artifacts/reports/ablation/ablation_report_template_ablation_package_scale-chain-6__v1.0.0.json
manifest_file=artifacts/reports/ablation/research_artifact_manifest_ablation_package_scale-chain-6__v1.0.0.json
```

**Key output fields:**
| Field | Meaning |
|---|---|
| `table_count` | Number of comparison tables generated (e.g. adaptive-vs-rule, observability ablation) |
| `containerized` | Whether a Docker execution profile was also emitted |
| `template_file` | JSON report template for paper writing |
| `manifest_file` | Research artifact manifest listing all generated files with hashes |

**All flags:**
```
--config CONFIG                             Preset JSON
--scenario SCENARIO                         Scenario JSON file
--seeds SEEDS                               Seeds
--horizon HORIZON                           Turns per run
--skip-ablations                            Only base conditions
--containerized                             Also emit a container execution profile
--container-image IMAGE                     Docker image name for the profile
--container-working-directory DIR           Working directory in container
--runs-root / --metrics-root / --reports-root
```

---

### `marbts-container-profile`

**What it does:** Resolves and optionally executes Docker Compose profiles for running MARBTS workflows inside a container. Use `--dry-run` to preview the exact Docker command without executing it.

**Sample run:**
```bash
# Preview the command (no Docker needed)
marbts-container-profile --spec multi_seed_baseline --dry-run

# Available specs
marbts-container-profile --spec ablation_report_baseline --dry-run
marbts-container-profile --spec policy_matrix_baseline --dry-run
marbts-container-profile --spec stress_suite_baseline --dry-run
```

**Sample output:**
```
CONTAINER_PROFILE_READY
timestamp_utc=2026-04-25T03:21:41.480529+00:00
spec_id=multi_seed_baseline
service_name=multi-seed-report
compose_profile=multi-seed
command=docker compose -f docker/docker-compose.yml --profile multi-seed run --rm multi-seed-report
marbts_command=multi-seed-report --config configs/experiments/multi_seed_baseline.json
dry_run=true
```

**All flags:**
```
--spec {ablation_report_baseline, multi_seed_baseline,
        policy_matrix_baseline, stress_suite_baseline}   Which workflow to run
--compose-file COMPOSE_FILE     Path to docker-compose.yml (default: docker/docker-compose.yml)
--docker-binary BINARY          Docker CLI executable (default: docker)
--build                         Build the image before running
--no-rm                         Don't pass --rm (container persists after run)
--dry-run                       Print command only, do not execute
```

---

### `marbts-release-validation`

**What it does:** Runs all 9 release-readiness gates and reports pass/fail for each. Used to verify the project is in a shippable state before tagging a release.

**Run:**
```bash
marbts-release-validation
```

**Output:**
```
RELEASE_READY
timestamp_utc=2026-04-25T03:21:33.346118+00:00
gate_count=9
pass_count=9
fail_count=0
all_gates_pass=true
  [PASS] packaging: version='0.6.0', entry_points=7
  [PASS] config_presets: preset_ids=multi_seed_baseline,...
  [PASS] seed_bundles: bundle_ids=rule_baseline_multi_seed,...
  [PASS] docker_assets: docker_files=2
  [PASS] notebook_assets: notebook_count=3, workflows=...
  [PASS] scripts_surface: script_count=13
  [PASS] stub_removal: checked_dirs=6
  [PASS] test_suite_coverage: test_file_count=8
  [PASS] readme_current: marker='run_release_validation'
```

**What each gate checks:**
| Gate | Checks |
|---|---|
| `packaging` | `pyproject.toml` version is set and all CLI entry points are wired |
| `config_presets` | All 4 experiment preset JSON files exist in `configs/experiments/` |
| `seed_bundles` | Seed bundle JSON files exist in `configs/seeds/` |
| `docker_assets` | `docker/Dockerfile` and `docker/docker-compose.yml` exist |
| `notebook_assets` | All 3 notebooks exist in `notebooks/` |
| `scripts_surface` | All smoke runner scripts exist in `scripts/` |
| `stub_removal` | No scaffold stubs remain in `docker/`, `notebooks/`, `configs/*` |
| `test_suite_coverage` | Minimum number of test files present |
| `readme_current` | README references the release validation command |

**Flags:**
```
--reports-root REPORTS_ROOT    Directory to write the readiness report JSON (optional)
```

---

## 6. Output and Artifact Layout

```
MARBTS/
├── output/
│   └── runs/
│       └── run_YYYYMMDD_HHMMSS_seed<N>.txt    ← plain-text log of every watch_sim.py run
│
├── artifacts/
│   ├── runs/
│   │   └── <run_id>/
│   │       ├── timesteps.jsonl      ← structured per-turn event log (JSON Lines)
│   │       ├── run_metadata.json    ← run provenance (seed, scenario, horizon, commit)
│   │       └── policy_metrics.json  ← per-agent action type counts
│   ├── metrics/
│   │   └── baseline_metrics_<run_id>.json
│   └── reports/
│       ├── multi_seed_report_<scenario>.json
│       ├── policy_experiment_matrix_<scenario>.json
│       ├── stress_test_suite_report.json
│       └── ablation/
│           ├── ablation_report_template_*.json
│           └── research_artifact_manifest_*.json
```

---

## 7. Scenario Library

| File | Nodes | Purpose |
|---|---|---|
| `scenarios/library/enterprise_medium.json` | 20 | Main scenario — 3-tier enterprise network (perimeter / internal / core), v2.0.0 |
| `scenarios/library/scale_chain_6.json` | 6 | Linear chain — minimal, fast runs, used in CI smoke tests |
| `scenarios/library/containment_stress.json` | 3 | Pre-breached — tests Blue containment under immediate threat |
| `scenarios/baselines/rule_baseline.json` | 4 | Rule-based baseline — fully deterministic, used for regression |

---

## Plan Revision Log

- 2026-04-25: Created `simulation_reference.md` with complete watch_sim.py command reference, per-turn field guide, outcome tier table, all CLI commands with sample outputs, and output/artifact layout.
