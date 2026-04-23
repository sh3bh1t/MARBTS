from __future__ import annotations

from datetime import datetime, timezone

from agents.adaptive import AdaptivePlanningPolicy
from agents.interfaces.policy import PolicyRegistry
from environment.graph_builder import build_graph_from_scenario
from hart.enums import ActorType
from hart.models import AdaptivePolicyConfig
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation


def main() -> None:
    scenario = load_scenario_file("scenarios/baselines/rule_baseline.json")
    graph = build_graph_from_scenario(scenario)

    deception_config = AdaptivePolicyConfig(
        planning_horizon=3,
        discount_factor=0.9,
        exploration_bias=0.0,
        enable_decoy=True,
        enable_bluff=True,
        deception_bias=1.0,
    )

    registry = PolicyRegistry()
    registry.register(AdaptivePlanningPolicy(actor=ActorType.RED, config=deception_config))
    registry.register(AdaptivePlanningPolicy(actor=ActorType.BLUE, config=deception_config))

    result = run_turn_based_simulation(
        graph,
        seed=20260424,
        horizon=3,
        scenario_id="phase5-deception-smoke",
        policy_registry=registry,
    )

    deception_events = 0
    for timestep in result.timesteps:
        red_event = timestep.red_action_intent.rationale_payload.get("deception_event")
        blue_event = timestep.blue_action_intent.rationale_payload.get("deception_event")
        if red_event is not None:
            deception_events += 1
        if blue_event is not None:
            deception_events += 1

    if deception_events == 0:
        raise RuntimeError("expected at least one deception_event in adaptive rationale payloads")

    print("DECEPTION_HOOKS_SMOKE_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"timesteps={len(result.timesteps)}")
    print(f"deception_events={deception_events}")


if __name__ == "__main__":
    main()
