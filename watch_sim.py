"""
watch_sim.py — Live MARBTS Red vs Blue simulation viewer.

Run from the MARBTS repo root — no PYTHONPATH setup needed.

QUICK START:
    python watch_sim.py                   # animated, 1.5 s/turn, enterprise-medium scenario
    python watch_sim.py --fast            # no delays, all turns at once
    python watch_sim.py --delay 3         # 3 seconds between turns
    python watch_sim.py --seed 42         # replay a specific run exactly
    python watch_sim.py --turns 30        # longer game
    python watch_sim.py --scenario rule_baseline  --policy rule   # tiny deterministic baseline
    python watch_sim.py --scenario containment_stress             # pre-breached 3-node network

Seeds are random by default — each run plays out differently.
Print the seed shown at the top, then pass --seed <N> to replay.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# --------------------------------------------------------------------------
# Make src/ importable without any shell PYTHONPATH hacks
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# --------------------------------------------------------------------------
# ANSI colours (Windows 10+, macOS, Linux)
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
# Scenarios and policy modes
# --------------------------------------------------------------------------
SCENARIO_MAP = {
    "enterprise_medium":  ROOT / "scenarios/library/enterprise_medium.json",
    "scale_chain_6":      ROOT / "scenarios/library/scale_chain_6.json",
    "containment_stress": ROOT / "scenarios/library/containment_stress.json",
    "rule_baseline":      ROOT / "scenarios/baselines/rule_baseline.json",
}

# Tier display groupings for enterprise_medium (v2.0.0 node names)
ENTERPRISE_TIERS = {
    "Perimeter  (sec 1-3)": ["01-ext", "02-iot1", "02-iot2", "02-web1", "02-web2", "03-mail", "03-proxy"],
    "Internal   (sec 3-5)": ["04-app1", "04-app2", "04-cache", "04-ci", "04-log", "05-apigw", "05-cloud"],
    "Core       (sec 6-9)": ["06-admin", "06-auth", "06-config", "07-dbback", "08-dbmain", "09-bastion"],
}


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

    from agents.adaptive.planning import AdaptivePlanningPolicy
    from hart.models import AdaptivePolicyConfig
    # Red: aggressive planner, high noise creates seed-dependent target choice
    red_cfg  = AdaptivePolicyConfig(exploration_bias=4.0, decision_noise=4.0)
    # Blue: reactive, reduced observability (acts on partial threat picture)
    # → sometimes patches crown-jewels preemptively, sometimes misses active breaches
    blue_cfg = AdaptivePolicyConfig(exploration_bias=2.5, decision_noise=3.5, reduced_observability=True)
    registry.register(AdaptivePlanningPolicy(actor=ActorType.RED,  config=red_cfg))
    registry.register(AdaptivePlanningPolicy(actor=ActorType.BLUE, config=blue_cfg))
    return registry, "AdaptivePlanningPolicy (Red)", "AdaptivePlanningPolicy (Blue)"


# --------------------------------------------------------------------------
# Printing helpers
# --------------------------------------------------------------------------

def _comp_icon(state: str) -> str:
    if state == "privileged": return _r("◼ PRIV  ")
    if state == "user":       return _r("▪ user  ")
    return _g("◻ clean ")

def _iso_tag(iso: bool) -> str:
    return _r(" ISOLATED") if iso else _dim(" live    ")

def _det_tag(det: str) -> str:
    if det == "detected":   return _y("detected  ")
    if det == "suspected":  return _y("suspected ")
    return _dim("undetected")

def bar(filled: int, total: int, width: int = 20) -> str:
    f = min(filled, total)
    b = "█" * f + "░" * (total - f)
    colour = _r if filled > 0 else _g
    return colour(f"[{b}]")


def print_banner(seed: int, scenario: str, red: str, blue: str, turns: int) -> None:
    print()
    print(_bold("=" * 70))
    print(_bold("  MARBTS  —  Red vs Blue Autonomous Cyber-Defense Simulation"))
    print(_bold("=" * 70))
    print(f"  Scenario : {scenario}")
    print(f"  Seed     : {_bold(str(seed))}  ← pass --seed {seed} to replay this exact run")
    print(f"  Turns    : {turns}")
    print(f"  {_r('RED')}  policy : {red}")
    print(f"  {_b('BLUE')} policy : {blue}")
    print()


def print_initial_topology(scenario_path: Path) -> None:
    import json
    data  = json.loads(scenario_path.read_text(encoding="utf-8"))
    nodes = data["nodes"]
    edges = data["edges"]

    print(_bold("  INITIAL NETWORK TOPOLOGY"))
    print("  " + "─" * 64)
    print(f"  {'NODE':<14}  {'TYPE':<10}  {'SERVICES':<18}  SEC  STATE")
    print("  " + "─" * 64)
    for n in nodes:
        svc  = ",".join(n.get("services", []))
        comp = n.get("compromised_state", "none")
        tag  = _r(f"⚠  {comp}") if comp != "none" else _dim("clean")
        print(f"  {n['node_id']:<14}  {n['node_type']:<10}  {svc:<18}  {n['security_level']:<4} {tag}")
    print()
    print(f"  {len(edges)} edges: ", end="")
    print("  ".join(f"{e['source']}→{e['target']}" for e in edges[:8]),
          "..." if len(edges) > 8 else "")
    print()


def print_network_state(graph, scenario_key: str, turn: int, total: int) -> None:
    """Print current node states grouped by tier for enterprise, flat list for others."""
    import networkx as nx

    print(f"  {'─' * 66}")
    print(f"  NETWORK STATE  turn {turn}/{total}")
    print(f"  {'─' * 66}")

    if scenario_key == "enterprise_medium":
        for tier_name, tier_nodes in ENTERPRISE_TIERS.items():
            print(f"  {_dim(tier_name)}")
            for nid in tier_nodes:
                if nid not in graph.nodes:
                    continue
                attrs = graph.nodes[nid]
                sec   = attrs.get("security_level", "?")
                print(f"    {nid:<14}  {_comp_icon(attrs.get('compromised_state','none'))}  "
                      f"{_det_tag(attrs.get('detection_state','undetected'))}  "
                      f"{_iso_tag(attrs.get('isolation_state', False))}  sec={sec}")
        print()
    else:
        for nid in sorted(graph.nodes()):
            attrs = graph.nodes[nid]
            sec   = attrs.get("security_level", "?")
            print(f"    {nid:<14}  {_comp_icon(attrs.get('compromised_state','none'))}  "
                  f"{_det_tag(attrs.get('detection_state','undetected'))}  "
                  f"{_iso_tag(attrs.get('isolation_state', False))}  sec={sec}")
        print()

    total_nodes = graph.number_of_nodes()
    comp = sum(1 for _, a in graph.nodes(data=True) if a.get("compromised_state") in {"user", "privileged"})
    iso  = sum(1 for _, a in graph.nodes(data=True) if a.get("isolation_state"))
    print(f"  Compromised: {bar(comp, total_nodes)} {comp}/{total_nodes}    "
          f"Isolated: {_dim(str(iso))}/{total_nodes}")
    print()


def _think(label: str, action_type: str, targets: str, delay: float, fast: bool) -> None:
    """Brief 'thinking' animation before revealing the decision."""
    if fast:
        return
    think_t = min(delay * 0.3, 0.6)
    print(f"  {label}  {_dim('analyzing...')}  ", end="", flush=True)
    time.sleep(think_t)
    print(f"\r  {label}  → chose {_bold(action_type.upper())} on {targets:<20}          ")


def print_turn(turn, graph_after, total_nodes: int,
               delay: float, fast: bool, turn_num: int, total: int,
               scenario_key: str) -> None:
    red_a  = turn.red_action_intent
    blue_a = turn.blue_action_intent
    metric = turn.metric_delta
    diff   = turn.post_state_diff

    print(_bold(f"\n{'─' * 70}"))
    print(_bold(f"  TURN {turn_num + 1} / {total}"))

    red_targets  = ", ".join(red_a.targets)  or "—"
    blue_targets = ", ".join(blue_a.targets) or "—"

    # --- Red thinking ---
    print()
    _think(_r("▶ RED "), red_a.action_type, red_targets, delay, fast)

    rp  = red_a.rationale_payload
    pt  = rp.get("planning_trace") or {}
    sc  = (rp.get("score_breakdown") or {}).get("components") or {}

    changed_tag = _r("✓ CHANGED") if red_a.changed else _dim("✗ blocked/no-op")
    print(f"  {_r('▶ RED')}   {_bold(red_a.action_type.upper()):<16}  → {red_targets}")
    print(f"       Rationale  : {red_a.rationale}")
    if rp.get("predicted_effect"):
        print(f"       Expected   : {rp['predicted_effect']}")
    if pt.get("cumulative_utility"):
        ves = pt.get("value_estimates") or []
        step_str = "  ".join(f"t+{v['step']}:{v['discounted_utility']:.2f}" for v in ves[:3])
        print(f"       Plan       : horizon={pt.get('horizon','?')}  "
              f"cumulative={pt.get('cumulative_utility','?')}  [{step_str}]")
    if rp.get("confidence"):
        print(f"       Confidence : {rp['confidence']:.2f}   utility={rp.get('utility_estimate',0):.2f}")
    print(f"       Outcome    : {changed_tag}  — {red_a.reason}")
    print()

    if not fast and delay > 0.3:
        time.sleep(delay * 0.3)

    # --- Blue thinking ---
    _think(_b("▶ BLUE"), blue_a.action_type, blue_targets, delay, fast)

    bp  = blue_a.rationale_payload
    bpt = bp.get("planning_trace") or {}

    blue_changed = _b("✓ CHANGED") if blue_a.changed else _dim("✗ blocked/no-op")
    print(f"  {_b('▶ BLUE')}  {_bold(blue_a.action_type.upper()):<16}  → {blue_targets}")
    print(f"       Rationale  : {blue_a.rationale}")
    if bp.get("predicted_effect"):
        print(f"       Expected   : {bp['predicted_effect']}")
    if bpt.get("cumulative_utility"):
        ves = bpt.get("value_estimates") or []
        step_str = "  ".join(f"t+{v['step']}:{v['discounted_utility']:.2f}" for v in ves[:3])
        print(f"       Plan       : horizon={bpt.get('horizon','?')}  "
              f"cumulative={bpt.get('cumulative_utility','?')}  [{step_str}]")
    if bp.get("confidence"):
        print(f"       Confidence : {bp['confidence']:.2f}   utility={bp.get('utility_estimate',0):.2f}")
    print(f"       Outcome    : {blue_changed}  — {blue_a.reason}")
    print()

    # --- State changes ---
    changed_nodes = diff.get("changed_nodes", [])
    removed_edges = diff.get("removed_edges", [])
    if changed_nodes or removed_edges:
        print(f"  {_y('Δ State changes this turn:')}")
        for cn in changed_nodes:
            nid   = cn["node_id"]
            parts = []
            for key in ("compromised_state", "detection_state", "isolation_state", "vulnerabilities", "security_level"):
                bv, av = cn["before"].get(key), cn["after"].get(key)
                if bv != av:
                    parts.append(f"{key}: {_dim(str(bv))} → {_y(str(av))}")
            if parts:
                print(f"    {_bold(nid)}: {' | '.join(parts)}")
        for edge in removed_edges:
            print(f"    {_r('edge severed:')} {edge[0]} ↔ {edge[1]}")
    else:
        print(f"  {_dim('  No state changes this turn.')}")
    print()

    # --- Score bar ---
    after_c  = metric.get("compromised_nodes_after", 0)
    before_c = metric.get("compromised_nodes_before", 0)
    delta    = metric.get("compromised_nodes_delta", 0)
    delta_s  = (
        _r(f"  ↑ +{delta} RED gains")  if delta > 0 else
        _b(f"  ↓ {delta} BLUE recovers") if delta < 0 else
        _dim("  — no change")
    )
    print(f"  Score: {bar(after_c, total_nodes)} {after_c}/{total_nodes} nodes compromised{delta_s}")

    if not fast and delay > 0:
        time.sleep(delay * 0.4)

    # Print current network state every 3 turns or when there are changes
    if changed_nodes or removed_edges or (turn_num + 1) % 5 == 0:
        print()
        print_network_state(graph_after, scenario_key, turn_num + 1, total)


def print_final_verdict(result, total_nodes: int, scenario_key: str) -> None:
    final_comp = sum(
        1 for _, attrs in result.final_graph.nodes(data=True)
        if attrs.get("compromised_state") in {"user", "privileged"}
    )
    priv_comp = sum(
        1 for _, attrs in result.final_graph.nodes(data=True)
        if attrs.get("compromised_state") == "privileged"
    )
    isolated = sum(
        1 for _, attrs in result.final_graph.nodes(data=True)
        if attrs.get("isolation_state") is True
    )
    red_actions   = sum(1 for t in result.timesteps if t.red_action_intent.changed)
    blue_actions  = sum(1 for t in result.timesteps if t.blue_action_intent.changed)

    print(_bold("\n" + "=" * 70))
    print(_bold("  FINAL VERDICT"))
    print(_bold("=" * 70))
    print()
    print(f"  Run ID      : {result.metadata.run_id}")
    print(f"  Scenario    : {result.metadata.scenario_id}")
    print(f"  Seed        : {result.metadata.seed}")
    print(f"  Turns played: {result.metadata.horizon}")
    print()
    print(f"  Compromised nodes     : {final_comp}/{total_nodes}  "
          f"(privileged: {priv_comp})")
    print(f"  Isolated nodes        : {isolated}/{total_nodes}")
    print(f"  Red state-changes     : {red_actions} / {result.metadata.horizon} turns")
    print(f"  Blue state-changes    : {blue_actions} / {result.metadata.horizon} turns")
    print()

    ratio = final_comp / total_nodes if total_nodes else 0
    if final_comp == 0:
        verdict = _b(_bold("  ✓ BLUE WINS  —  network fully defended. No nodes compromised."))
    elif ratio < 0.30:     # < 6/20
        verdict = _b(_bold(f"  ✓ BLUE HOLDS  —  breach contained to {final_comp}/{total_nodes} nodes. Core intact."))
    elif ratio < 0.45:     # 6-8/20
        verdict = _b(f"  ↓ BLUE ADVANTAGE  —  {final_comp}/{total_nodes} nodes compromised. Red contained at perimeter.")
    elif ratio < 0.60:     # 9-11/20
        verdict = _y(f"  ⚔  CONTESTED  —  {final_comp}/{total_nodes} nodes compromised. Battle undecided.")
    elif ratio < 0.70:     # 12-13/20
        verdict = _r(f"  ↑ RED ADVANTAGE  —  {final_comp}/{total_nodes} nodes breached. Core under pressure.")
    else:                  # >= 14/20
        verdict = _r(_bold(f"  ✗ RED WINS  —  critical breach. {final_comp}/{total_nodes} nodes compromised."))
    print(verdict)
    print()

    print("  Final network state:")
    print_network_state(result.final_graph, scenario_key, result.metadata.horizon, result.metadata.horizon)

    print(_bold("=" * 70))
    print()
    run_dir = f"artifacts/runs/{result.metadata.run_id}"
    print(f"  Artifacts saved to: {run_dir}/")
    print(f"    timesteps.jsonl      ← full turn log (JSON Lines)")
    print(f"    run_metadata.json    ← run provenance + seed")
    print(f"    policy_metrics.json  ← action counts per agent")
    print()
    print(f"  Replay this run:  python watch_sim.py --seed {result.metadata.seed} --fast")
    print()


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Watch MARBTS Red vs Blue autonomous simulation live.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--scenario", choices=list(SCENARIO_MAP), default="enterprise_medium",
        help="Network scenario (default: enterprise_medium — 20 nodes, varied security levels)",
    )
    parser.add_argument(
        "--policy", choices=["adaptive", "rule"], default="adaptive",
        help="adaptive = AdaptivePlanningPolicy (default); rule = deterministic rule-based",
    )
    parser.add_argument(
        "--turns", type=int, default=20,
        help="Number of simulation turns (default: 20)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="RNG seed for reproducibility (default: random — different each run)",
    )
    parser.add_argument(
        "--delay", type=float, default=1.5,
        help="Seconds between turns for the animated display (default: 1.5)",
    )
    parser.add_argument(
        "--fast", action="store_true",
        help="Skip all delays — run to completion instantly",
    )
    parser.add_argument(
        "--no-resistance", action="store_true",
        help="Disable exploit resistance (exploits always succeed; less variable)",
    )
    args = parser.parse_args()

    # Enable ANSI on Windows
    if sys.platform == "win32":
        import os
        os.system("")

    # Random seed if not specified
    seed = args.seed if args.seed is not None else int(time.time()) % (2 ** 31 - 1)
    exploit_resistance = not args.no_resistance

    from environment.graph_builder import build_graph_from_scenario
    from schemas.scenario import load_scenario_file
    from simulation.kernel import run_turn_based_simulation
    from simulation.log_writer import write_run_artifacts
    from metrics.baseline_metrics import write_baseline_metrics_artifact

    scenario_path = SCENARIO_MAP[args.scenario]
    registry, red_name, blue_name = _build_registry(args.policy)

    print_banner(seed, args.scenario, red_name, blue_name, args.turns)
    print_initial_topology(scenario_path)

    if not args.fast:
        print(_dim(f"  Initialising — exploit resistance: {'ON' if exploit_resistance else 'OFF'} — "
                   f"delay: {args.delay}s/turn"))
        print(_dim("  (use --fast to skip delays, --seed N to replay)"))
        print()
        time.sleep(0.5)

    scenario = load_scenario_file(scenario_path)
    graph    = build_graph_from_scenario(scenario)
    total_nodes = graph.number_of_nodes()

    try:
        result = run_turn_based_simulation(
            graph,
            seed=seed,
            horizon=args.turns,
            scenario_id=scenario.metadata.scenario_id,
            policy_registry=registry,
            exploit_resistance=exploit_resistance,
        )
    except RuntimeError as exc:
        if "no legal actions" in str(exc):
            print()
            print(_b(_bold("  All nodes isolated — Blue achieved total containment.")))
            print(_dim(f"  ({exc})"))
            sys.exit(0)
        raise

    # Write artifacts
    write_run_artifacts(result, ROOT / "artifacts/runs")
    write_baseline_metrics_artifact(result, ROOT / "artifacts/metrics")

    if not args.fast:
        print(_dim(f"  Simulation complete. Animating {len(result.timesteps)} turns...\n"))
        time.sleep(0.3)

    try:
        for i, turn in enumerate(result.timesteps):
            graph_at_turn = result.graph_snapshots[i] if i < len(result.graph_snapshots) else result.final_graph
            print_turn(turn, graph_at_turn, total_nodes,
                       args.delay, args.fast, i, args.turns, args.scenario)
    except KeyboardInterrupt:
        print("\n\n  [Ctrl+C — skipping to verdict]\n")

    print_final_verdict(result, total_nodes, args.scenario)


if __name__ == "__main__":
    main()
