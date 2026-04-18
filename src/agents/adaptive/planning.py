from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

import networkx as nx

from agents.adaptive.ablation import apply_observability_filter, effective_planning_depth
from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyDecision
from agents.red.rule_based import RuleBasedRedPolicy
from environment.legal_actions import LegalAction, get_legal_actions
from hart.enums import ActorType
from hart.models import (
    AdaptivePolicyConfig,
    DecisionRationale,
    PlanningTrace,
    PolicyContext,
    PolicyMetricsSnapshot,
    PolicyScoreBreakdown,
    ValueEstimate,
)
from simulation.graph_codec import graph_from_snapshot_payload
from simulation.state_diff import snapshot_payload
from simulation.turn_resolution import apply_actor_action, count_compromised_nodes


class AdaptivePlanningPolicy:
    def __init__(
        self,
        actor: ActorType,
        config: AdaptivePolicyConfig | None = None,
    ) -> None:
        self.actor = actor
        self.config = config or AdaptivePolicyConfig()
        self.name = f"adaptive_planner_{actor.value}_v1"
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)

    def _fresh_opponent_policy(self):
        if self.actor == ActorType.RED:
            return RuleBasedBluePolicy()
        return RuleBasedRedPolicy()

    def _other_actor(self) -> ActorType:
        return ActorType.BLUE if self.actor == ActorType.RED else ActorType.RED

    def _metrics_snapshot(self) -> PolicyMetricsSnapshot:
        return PolicyMetricsSnapshot(
            policy_name=self.name,
            actions_selected=self._actions_selected,
            action_type_counts=dict(sorted(self._action_type_counts.items())),
        )

    def _state_utility(self, graph: nx.Graph) -> float:
        compromised = 0
        privileged = 0
        isolated = 0
        decoy_degree_total = 0
        feint_degree_total = 0
        security_total = 0

        for node_id, attrs in graph.nodes(data=True):
            state = attrs.get("compromised_state")
            if state in {"user", "privileged"}:
                compromised += 1
            if state == "privileged":
                privileged += 1
            if attrs.get("isolation_state"):
                isolated += 1
            if attrs.get("decoy_state"):
                decoy_degree_total += graph.degree(node_id)
            if attrs.get("feint_state"):
                feint_degree_total += graph.degree(node_id)
            security_total += int(attrs.get("security_level", 0))

        edge_count = graph.number_of_edges()

        if self.actor == ActorType.RED:
            return round((compromised * 12.0) + (privileged * 8.0) + (edge_count * 0.5) - (isolated * 5.0), 3)

        return round(
            (security_total * 0.4)
            + (isolated * 4.0)
            + (decoy_degree_total * (3.0 if self.config.feature_flags.get("prefer_decoy", False) else 0.75))
            + (feint_degree_total * (2.5 if self.config.feature_flags.get("prefer_feint", False) else 0.6))
            - (compromised * 12.0)
            - (privileged * 9.0)
            - (edge_count * 0.25),
            3,
        )

    def _confidence(self, candidate_utility: float, baseline_utility: float) -> float:
        improvement = max(candidate_utility - baseline_utility, 0.0)
        bounded = min(improvement / 20.0, 1.0)
        return round(0.45 + (bounded * 0.5), 3)

    def _plan_future_self_turn(
        self,
        graph: nx.Graph,
        *,
        scenario_id: str,
        seed: int,
        timestep: int,
        remaining_depth: int,
    ) -> float:
        if remaining_depth <= 0:
            return self._state_utility(graph)

        legal_actions = get_legal_actions(graph, self.actor)
        if not legal_actions:
            return self._state_utility(graph)

        best_utility = float("-inf")
        for action in legal_actions:
            next_graph, _ = apply_actor_action(graph, self.actor, action)
            utility = self._simulate_after_self_action(
                next_graph,
                scenario_id=scenario_id,
                seed=seed,
                timestep=timestep,
                remaining_depth=remaining_depth - 1,
            )
            if utility > best_utility:
                best_utility = utility
        return best_utility

    def _simulate_after_self_action(
        self,
        graph: nx.Graph,
        *,
        scenario_id: str,
        seed: int,
        timestep: int,
        remaining_depth: int,
    ) -> float:
        if remaining_depth <= 0:
            return self._state_utility(graph)

        opponent_actor = self._other_actor()
        opponent_legal_actions = get_legal_actions(graph, opponent_actor)
        if opponent_legal_actions:
            opponent_context = PolicyContext(
                actor=opponent_actor,
                timestep=timestep + 1,
                scenario_id=scenario_id,
                seed=seed,
                compromised_nodes=count_compromised_nodes(graph),
                policy_metrics={},
                state_snapshot=snapshot_payload(graph),
            )
            opponent_decision = self._fresh_opponent_policy().select_action(opponent_context, opponent_legal_actions)
            graph, _ = apply_actor_action(graph, opponent_actor, opponent_decision.action)

        return self._plan_future_self_turn(
            graph,
            scenario_id=scenario_id,
            seed=seed,
            timestep=timestep + 1,
            remaining_depth=remaining_depth - 1,
        )

    def select_action(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...]) -> PolicyDecision:
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")
        if not context.state_snapshot:
            raise ValueError("adaptive planning requires PolicyContext.state_snapshot")

        if self.config.feature_flags.get("no_decoy", False):
            legal_actions = tuple(action for action in legal_actions if action.action_type.value != "decoy")
        if self.config.feature_flags.get("no_feint", False):
            legal_actions = tuple(action for action in legal_actions if action.action_type.value != "feint")
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty after feature-flag filtering")

        visible_snapshot = apply_observability_filter(context.state_snapshot, self.config)
        current_graph = graph_from_snapshot_payload(visible_snapshot)
        baseline_utility = self._state_utility(current_graph)
        planning_depth = effective_planning_depth(self.config)

        candidate_values: list[ValueEstimate] = []
        ranked: list[tuple[float, str, tuple[str, ...], LegalAction, float]] = []
        for action in legal_actions:
            next_graph, _ = apply_actor_action(current_graph, self.actor, action)
            utility = self._simulate_after_self_action(
                next_graph,
                scenario_id=context.scenario_id,
                seed=context.seed,
                timestep=context.timestep,
                remaining_depth=max(planning_depth - 1, 0),
            )
            confidence = self._confidence(utility, baseline_utility)
            candidate_values.append(
                ValueEstimate(
                    action_type=action.action_type.value,
                    targets=action.targets,
                    utility=utility,
                    confidence=confidence,
                    summary=f"projected utility {utility:.3f} after bounded rollout",
                )
            )
            ranked.append((utility, action.action_type.value, action.targets, action, confidence))

        ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
        selected_utility, _, _, selected_action, selected_confidence = ranked[0]

        self._actions_selected += 1
        self._action_type_counts[selected_action.action_type.value] += 1

        planning_trace = PlanningTrace(
            planning_depth=planning_depth,
            selected_action=selected_action.action_type.value,
            candidate_values=tuple(candidate_values),
            notes=(
                f"planning_mode={self.config.planning_mode}",
                f"opponent_policy={self.config.opponent_policy_name}",
                f"reduced_observability={self.config.feature_flags.get('reduced_observability', False)}",
                f"no_planning={self.config.feature_flags.get('no_planning', False)}",
                f"prefer_decoy={self.config.feature_flags.get('prefer_decoy', False)}",
                f"prefer_feint={self.config.feature_flags.get('prefer_feint', False)}",
                f"no_feint={self.config.feature_flags.get('no_feint', False)}",
                "deterministic rollout uses sandboxed legal action space only",
            ),
        )

        rationale = DecisionRationale(
            policy_name=self.name,
            summary=f"selected {selected_action.action_type.value} via deterministic bounded rollout planning",
            predicted_effect=f"optimize {self.actor.value} utility across a bounded multi-step simulation",
            confidence=selected_confidence,
            utility_estimate=selected_utility,
            score_breakdown=PolicyScoreBreakdown(
                total_score=selected_utility,
                components={
                    "projected_state_utility": selected_utility,
                    "baseline_state_utility": baseline_utility,
                    "planning_depth": float(planning_depth),
                },
            ),
            tie_breaker="(-utility, action_type, targets)",
            trace=asdict(planning_trace),
        )

        return PolicyDecision(
            action=selected_action,
            rationale=rationale,
            metrics_snapshot=self._metrics_snapshot(),
        )
