"""
watch_sim.py — Live turn-by-turn MARBTS simulation viewer.

Run from the MARBTS repo root:
    python watch_sim.py                          # default: adaptive policies, containment_stress scenario
    python watch_sim.py --auto                   # no pauses, run to completion
    python watch_sim.py --turns 12               # 12 turns instead of default 8
    python watch_sim.py --policy rule            # use simpler rule-based policies
    python watch_sim.py --scenario rule_baseline # use the 4-node baseline scenario

No PYTHONPATH env-var needed — this script sets it automatically.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# Make src/ importable without setting PYTHONPATH externally
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# --------------------------------------------------------------------------
# ANSI colour helpers (work on Windows 10+ / macOS / Linux terminals)
# --------------------------------------------------------------------------
RED    = "\033[91m"
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RESET  = "\033[0m"

def _r(t: str) -> str: return f"{RED}{t}{RESET}"
def _b(t: str) -> str: return f"{BLUE}{t}{RESET}"
def _g(t: str) -> str: return f"{GREEN}{t}{RESET}"
def _y(t: str) -> str: return f"{YELLOW}{t}{RESET}"
def _bold(t: str) -> str: return f"{BOLD}{t}{RESET}"
def _dim(t: str) -> str: return f"{DIM}{t}{RESET}"


# --------------------------------------------------------------------------
# Scenario / policy helpers
# --------------------------------------------------------------------------
SCENARIO_MAP = {
    "containment_stress": ROOT / "scenarios/library/containment_stress.json",
    "rule_baseline":      ROOT / "scenarios/baselines/rule_baseline.json",
    "scale_chain_6":      ROOT / "scenarios/library/scale_chain_6.json",
}

DEFAULT_SCENARIO = "scale_chain_6"
DEFAULT_SEED     = 20260329


def _build_registry(policy_mode: str):
    from agents.interfaces.policy import PolicyRegistry
    from hart.enums import ActorType

    registry = PolicyRegistry()

    if policy_mode == "rule":
        from agents.red.rule_based import RuleBasedRedPolicy
        from agents.blue.rule_based import RuleBasedBluePolicy
        registry.register(RuleBasedRedPolicy())
        registry.register(RuleBasedBluePolicy())
        return registry, "RuleBasedRedPolicy", "RuleBasedBluePolicy"

    # adaptive (default) or mixed
    from agents.adaptive.planning import AdaptivePlanningPolicy
    from hart.models import AdaptivePolicyConfig
    red = AdaptivePlanningPolicy(actor=ActorType.RED,  config=AdaptivePolicyConfig())
    registry.register(red)

    if policy_mode == "mixed":
        from agents.blue.rule_based import RuleBasedBluePolicy
        registry.register(RuleBasedBluePolicy())
        return registry, "AdaptivePlanningPolicy", "RuleBasedBluePolicy"

    blue = AdaptivePlanningPolicy(actor=ActorType.BLUE, config=AdaptivePolicyConfig())
    registry.register(blue)
    return registry, "AdaptivePlanningPolicy", "AdaptivePlanningPolicy"


# --------------------------------------------------------------------------
# Printing helpers
# --------------------------------------------------------------------------

def print_banner() -> None:
    print()
    print(_bold("=" * 68))
    print(_bold("  MARBTS  —  Red vs Blue Autonomous Cyber Defense Simulation"))
    print(_bold("=" * 68))
    print()


def print_scenario_header(scenario_path: Path, red_policy: str, blue_policy: str,
                          turns: int, seed: int) -> None:
    import json
    data = json.loads(scenario_path.read_text(encoding="utf-8"))
    nodes  = data["nodes"]
    edges  = data["edges"]
    sid    = data["metadata"]["scenario_id"]

    print(_bold(f"  Scenario : {sid}"))
    print(f"  Red      : {_r(red_policy)}")
    print(f"  Blue     : {_b(blue_policy)}")
    print(f"  Turns    : {turns}   Seed: {seed}")
    print()
    print(_bold("  NETWORK TOPOLOGY"))
    print("  " + "─" * 60)
    print(f"  {'NODE':<14}  {'TYPE':<10}  {'SERVICES':<18}  SEC  INITIAL STATE")
    print("  " + "─" * 60)
    for n in nodes:
        services = ",".join(n.get("services", []))
        comp     = n.get("compromised_state", "none")
        comp_str = _r(f"compromised:{comp}") if comp != "none" else _dim("clean")
        print(f"  {n['node_id']:<14}  {n['node_type']:<10}  {services:<18}  {n['security_level']}    {comp_str}")
    print()
    print("  Edges: " + "  |  ".join(f"{e['source']} → {e['target']}" for e in edges))
    print()


def _comp_bar(count: int, total: int) -> str:
    bar = "█" * count + "░" * (total - count)
    colour = _r if count > 0 else _g
    return colour(f"[{bar}]")


def print_turn(turn, total_nodes: int, auto: bool, turn_num: int, total: int) -> None:
    red_a  = turn.red_action_intent
    blue_a = turn.blue_action_intent
    metric = turn.metric_delta
    diff   = turn.post_state_diff

    print(_bold(f"{'─' * 68}"))
    print(_bold(f"  TURN {turn_num + 1} of {total}"))
    print()

    # ── RED ──────────────────────────────────────────────────────────────
    targets_str = ", ".join(red_a.targets) or "—"
    changed_tag = _r("✓ CHANGED") if red_a.changed else _dim("✗ no change")
    print(f"  {_r('▶ RED')}   {_bold(red_a.action_type.upper()):<16}  target: {targets_str}")
    rp = red_a.rationale_payload
    print(f"       Why   : {red_a.rationale}")
    if "predicted_effect" in rp:
        print(f"       Effect: {rp['predicted_effect']}")
    if "planning_trace" in rp and rp["planning_trace"]:
        pt = rp["planning_trace"]
        print(f"       Plan  : horizon={pt.get('horizon','?')}  cumulative_utility={pt.get('cumulative_utility','?')}")
    if "confidence" in rp:
        print(f"       Score : confidence={rp['confidence']:.2f}  utility={rp.get('utility_estimate', 0):.2f}")
    print(f"       State : {changed_tag}  — {red_a.reason}")
    print()

    # ── BLUE ─────────────────────────────────────────────────────────────
    blue_targets = ", ".join(blue_a.targets) or "—"
    blue_changed = _b("✓ CHANGED") if blue_a.changed else _dim("✗ no change")
    print(f"  {_b('▶ BLUE')}  {_bold(blue_a.action_type.upper()):<16}  target: {blue_targets}")
    bp = blue_a.rationale_payload
    print(f"       Why   : {blue_a.rationale}")
    if "predicted_effect" in bp:
        print(f"       Effect: {bp['predicted_effect']}")
    if "planning_trace" in bp and bp["planning_trace"]:
        pt = bp["planning_trace"]
        print(f"       Plan  : horizon={pt.get('horizon','?')}  cumulative_utility={pt.get('cumulative_utility','?')}")
    if "confidence" in bp:
        print(f"       Score : confidence={bp['confidence']:.2f}  utility={bp.get('utility_estimate', 0):.2f}")
    print(f"       State : {blue_changed}  — {blue_a.reason}")
    print()

    # ── Network state changes ─────────────────────────────────────────────
    changed_nodes = diff.get("changed_nodes", [])
    removed_edges = diff.get("removed_edges", [])
    if changed_nodes or removed_edges:
        print(f"  {_y('Δ Network changes:')}")
        for cn in changed_nodes:
            nid   = cn["node_id"]
            parts = []
            for key in ("compromised_state", "detection_state", "isolation_state", "vulnerabilities"):
                bv = cn["before"].get(key)
                av = cn["after"].get(key)
                if bv != av:
                    parts.append(f"{key}: {_dim(str(bv))} → {_y(str(av))}")
            if parts:
                print(f"    {_bold(nid)}: {' | '.join(parts)}")
        for edge in removed_edges:
            print(f"    {_r('edge cut:')} {edge[0]} ↔ {edge[1]}")
    else:
        print(f"  {_dim('  No network state changes this turn.')}")
    print()

    # ── Score bar ─────────────────────────────────────────────────────────
    after_c = metric.get("compromised_nodes_after", 0)
    delta   = metric.get("compromised_nodes_delta", 0)
    bar     = _comp_bar(after_c, total_nodes)
    delta_s = (
        _r(f"  (+{delta} red gain)")  if delta > 0 else
        _b(f"  ({delta} blue recov)") if delta < 0 else
        _dim("  (no change)")
    )
    print(f"  Compromised: {bar} {after_c}/{total_nodes}{delta_s}")
    print()

    if not auto:
        try:
            input(_dim("  ── Press Enter for next turn  (Ctrl+C to skip to verdict) ──  "))
        except (EOFError, KeyboardInterrupt):
            print()
            raise


def print_final_verdict(result, total_nodes: int) -> None:
    final_compromised = sum(
        1 for _, attrs in result.final_graph.nodes(data=True)
        if attrs.get("compromised_state") in {"user", "privileged"}
    )
    isolated = sum(
        1 for _, attrs in result.final_graph.nodes(data=True)
        if attrs.get("isolation_state") is True
    )

    print(_bold("=" * 68))
    print(_bold("  FINAL VERDICT"))
    print(_bold("=" * 68))
    print()
    print(f"  Run ID   : {result.metadata.run_id}")
    print(f"  Scenario : {result.metadata.scenario_id}")
    print(f"  Seed     : {result.metadata.seed}")
    print(f"  Turns    : {result.metadata.horizon}")
    print()

    bar = _comp_bar(final_compromised, total_nodes)
    print(f"  Compromised: {bar} {final_compromised}/{total_nodes} nodes")
    print(f"  Isolated:    {isolated}/{total_nodes} nodes")
    print()

    if final_compromised == 0:
        print(_b(_bold("  RESULT → BLUE WINS  —  network fully defended.")))
    elif final_compromised == total_nodes:
        print(_r(_bold("  RESULT → RED WINS   —  full network compromise.")))
    elif final_compromised / total_nodes >= 0.5:
        print(_r(_bold(f"  RESULT → RED ADVANTAGE  ({final_compromised}/{total_nodes} nodes compromised)")))
    else:
        print(_b(_bold(f"  RESULT → BLUE ADVANTAGE  (only {final_compromised}/{total_nodes} nodes compromised)")))
    print()

    print("  Final node states:")
    print("  " + "─" * 52)
    for node_id in sorted(result.final_graph.nodes()):
        attrs  = result.final_graph.nodes[node_id]
        comp   = attrs.get("compromised_state", "none")
        det    = attrs.get("detection_state", "undetected")
        iso    = attrs.get("isolation_state", False)
        c_str  = _r(f"  {comp:<12}") if comp != "none" else _g(f"  {comp:<12}")
        d_str  = _y(f"  {det:<12}") if det == "detected" else _dim(f"  {det:<12}")
        i_str  = _r("  ISOLATED") if iso else _dim("  live")
        print(f"  {node_id:<14}{c_str}{d_str}{i_str}")
    print()

    print(_bold("=" * 68))
    print()
    print(f"  Artifacts: artifacts/runs/{result.metadata.run_id}/")
    print(f"    timesteps.jsonl      ← full turn log  (one JSON object per line)")
    print(f"    run_metadata.json    ← provenance")
    print(f"    policy_metrics.json  ← per-agent action counts")
    print()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Watch MARBTS Red vs Blue simulation live.")
    parser.add_argument("--auto",     action="store_true",
                        help="Run all turns without pausing (default: pause between turns)")
    parser.add_argument("--turns",    type=int, default=6,
                        help="Number of simulation turns (default: 6)")
    parser.add_argument("--policy",   choices=["adaptive", "rule", "mixed"], default="adaptive",
                        help="adaptive = AdaptivePlanningPolicy for both (default); "
                             "rule = RuleBasedPolicy for both; "
                             "mixed = adaptive Red vs rule Blue")
    parser.add_argument("--scenario", choices=list(SCENARIO_MAP), default=DEFAULT_SCENARIO,
                        help=f"Scenario to run (default: {DEFAULT_SCENARIO})")
    parser.add_argument("--seed",     type=int, default=DEFAULT_SEED,
                        help=f"RNG seed (default: {DEFAULT_SEED})")
    args = parser.parse_args()

    # Enable ANSI colour on Windows
    if sys.platform == "win32":
        import os
        os.system("")

    from environment.graph_builder import build_graph_from_scenario
    from schemas.scenario import load_scenario_file
    from simulation.kernel import run_turn_based_simulation
    from simulation.log_writer import write_run_artifacts
    from metrics.baseline_metrics import write_baseline_metrics_artifact

    scenario_path = SCENARIO_MAP[args.scenario]
    registry, red_policy_name, blue_policy_name = _build_registry(args.policy)

    print_banner()
    print_scenario_header(scenario_path, red_policy_name, blue_policy_name,
                          args.turns if args.turns else 6, args.seed)

    print(_dim("  Initialising simulation..."))
    scenario = load_scenario_file(scenario_path)
    graph    = build_graph_from_scenario(scenario)
    total_nodes = graph.number_of_nodes()

    # With fully-isolating Blue policies, a run of N turns can exhaust all N nodes.
    # Cap the horizon to the node count to prevent "no legal actions" errors.
    effective_turns = min(args.turns, total_nodes)
    if effective_turns < args.turns:
        print(_dim(f"  (capping turns to {effective_turns} — matches node count for this scenario)"))

    try:
        result = run_turn_based_simulation(
            graph,
            seed=args.seed,
            horizon=effective_turns,
            scenario_id=scenario.metadata.scenario_id,
            policy_registry=registry,
        )
    except RuntimeError as exc:
        if "no legal actions" in str(exc):
            print(_r(f"\n  Simulation ended early: {exc}"))
            print(_b("  All nodes are isolated — Blue has achieved total containment."))
            sys.exit(0)
        raise

    # Write artifacts
    write_run_artifacts(result, ROOT / "artifacts/runs")
    write_baseline_metrics_artifact(result, ROOT / "artifacts/metrics")

    print(_bold(f"\n  Ready — {effective_turns} turns to replay.\n"))
    if not args.auto:
        print(_dim("  (Press Enter after each turn   |   Ctrl+C to jump to verdict)\n"))

    try:
        for i, turn in enumerate(result.timesteps):
            print_turn(turn, total_nodes, args.auto, i, args.turns)
    except KeyboardInterrupt:
        print("\n\n  [skipped to final verdict]\n")

    print_final_verdict(result, total_nodes)


if __name__ == "__main__":
    main()
