from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict

from agents.adaptive.ablation import apply_observability_filter
from agents.interfaces.policy import PolicyDecision
from environment.legal_actions import LegalAction
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


class RLBaselinePolicy:
    def __init__(
        self,
        actor: ActorType,
        config: AdaptivePolicyConfig | None = None,
    ) -> None:
        self.actor = actor
        self.config = config or AdaptivePolicyConfig(backend="rl", model_name="value_q_v1")
        self.name = f"rl_baseline_{actor.value}_v1"
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)

    def _metrics_snapshot(self) -> PolicyMetricsSnapshot:
        return PolicyMetricsSnapshot(
            policy_name=self.name,
            actions_selected=self._actions_selected,
            action_type_counts=dict(sorted(self._action_type_counts.items())),
        )

    def _red_action_components(self, action: LegalAction, node_attrs: dict, graph_degree: int, compromised_nodes: int) -> dict[str, float]:
        vulnerabilities = len(node_attrs.get("vulnerabilities", []))
        compromised_state = str(node_attrs.get("compromised_state", "none"))
        privileged_bonus = 6.0 if compromised_state == "user" and action.action_type.value == "escalate" else 0.0
        lateral_bonus = 0.0
        if action.action_type.value == "lateral_move":
            target_attrs = node_attrs
            target_state = str(target_attrs.get("compromised_state", "none"))
            lateral_bonus = 5.5 if target_state == "none" else 1.5

        base = {
            "scan": 4.5,
            "exploit": 8.5,
            "lateral_move": 7.5,
            "escalate": 7.0,
        }.get(action.action_type.value, 0.0)
        return {
            "base_q": base,
            "vulnerability_signal": float(vulnerabilities) * 1.6,
            "graph_reachability": float(graph_degree) * 0.8,
            "current_pressure": float(compromised_nodes) * 0.3,
            "privilege_bonus": privileged_bonus,
            "lateral_bonus": lateral_bonus,
        }

    def _blue_action_components(self, action: LegalAction, node_attrs: dict, graph_degree: int, compromised_nodes: int) -> dict[str, float]:
        vulnerabilities = len(node_attrs.get("vulnerabilities", []))
        compromised_state = str(node_attrs.get("compromised_state", "none"))
        detection_state = str(node_attrs.get("detection_state", "undetected"))
        security_level = int(node_attrs.get("security_level", 0))

        compromised_bonus = 6.0 if compromised_state in {"user", "privileged"} else 0.0
        detection_bonus = 2.5 if detection_state in {"suspected", "confirmed"} else 0.5
        base = {
            "monitor": 4.0,
            "patch": 7.8,
            "block": 7.2,
            "isolate": 7.0,
            "decoy": 5.8,
            "feint": 5.4,
        }.get(action.action_type.value, 0.0)
        deception_bias = 0.0
        if action.action_type.value == "decoy":
            deception_bias = 2.8 if self.config.feature_flags.get("prefer_decoy", False) else 1.2
        if action.action_type.value == "feint":
            deception_bias = 2.6 if self.config.feature_flags.get("prefer_feint", False) else 1.0

        containment_bonus = 0.0
        if action.action_type.value in {"block", "isolate"}:
            containment_bonus = 2.5 + (float(compromised_nodes) * 1.4)

        return {
            "base_q": base,
            "compromise_pressure": float(compromised_nodes) * 1.2,
            "compromised_bonus": compromised_bonus,
            "vulnerability_signal": float(vulnerabilities) * 1.3,
            "detection_bonus": detection_bonus,
            "security_gap": float(max(10 - security_level, 0)) * 0.35,
            "network_centrality_proxy": float(graph_degree) * 0.6,
            "containment_bonus": containment_bonus,
            "deception_bias": deception_bias,
        }

    def _score_action(self, graph, action: LegalAction, context: PolicyContext) -> tuple[float, dict[str, float]]:
        if len(action.targets) == 1:
            node_id = action.targets[0]
        else:
            node_id = action.targets[-1]
        node_attrs = dict(graph.nodes[node_id])
        graph_degree = graph.degree(node_id)
        if self.actor == ActorType.RED:
            components = self._red_action_components(action, node_attrs, graph_degree, context.compromised_nodes)
        else:
            components = self._blue_action_components(action, node_attrs, graph_degree, context.compromised_nodes)
        total_score = round(sum(components.values()), 3)
        return total_score, components

    def select_action(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...]) -> PolicyDecision:
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")
        if not context.state_snapshot:
            raise ValueError("rl baseline requires PolicyContext.state_snapshot")

        if self.config.feature_flags.get("no_decoy", False):
            legal_actions = tuple(action for action in legal_actions if action.action_type.value != "decoy")
        if self.config.feature_flags.get("no_feint", False):
            legal_actions = tuple(action for action in legal_actions if action.action_type.value != "feint")
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty after feature-flag filtering")

        visible_snapshot = apply_observability_filter(context.state_snapshot, self.config)
        graph = graph_from_snapshot_payload(visible_snapshot)

        ranked: list[tuple[float, str, tuple[str, ...], LegalAction, dict[str, float]]] = []
        candidate_values: list[ValueEstimate] = []
        for action in legal_actions:
            total_score, components = self._score_action(graph, action, context)
            confidence = round(0.45 + min(total_score, 20.0) / 40.0, 3)
            candidate_values.append(
                ValueEstimate(
                    action_type=action.action_type.value,
                    targets=action.targets,
                    utility=total_score,
                    confidence=confidence,
                    summary=f"approximate q-value {total_score:.3f} from deterministic feature weights",
                )
            )
            ranked.append((total_score, action.action_type.value, action.targets, action, components))

        ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
        selected_score, _, _, selected_action, selected_components = ranked[0]

        self._actions_selected += 1
        self._action_type_counts[selected_action.action_type.value] += 1

        trace = PlanningTrace(
            planning_depth=0,
            selected_action=selected_action.action_type.value,
            candidate_values=tuple(candidate_values),
            notes=(
                "policy_mode=deterministic_value_q",
                f"reduced_observability={self.config.feature_flags.get('reduced_observability', False)}",
                f"no_decoy={self.config.feature_flags.get('no_decoy', False)}",
                f"no_feint={self.config.feature_flags.get('no_feint', False)}",
                f"prefer_decoy={self.config.feature_flags.get('prefer_decoy', False)}",
                f"prefer_feint={self.config.feature_flags.get('prefer_feint', False)}",
            ),
        )

        rationale = DecisionRationale(
            policy_name=self.name,
            summary=f"selected {selected_action.action_type.value} via deterministic RL-style value ranking",
            predicted_effect="maximize approximate long-run actor utility from fixed q-value feature weights",
            confidence=round(0.45 + min(selected_score, 20.0) / 40.0, 3),
            utility_estimate=selected_score,
            score_breakdown=PolicyScoreBreakdown(
                total_score=selected_score,
                components=selected_components,
            ),
            tie_breaker="(-q_value, action_type, targets)",
            trace=asdict(trace),
        )
        return PolicyDecision(
            action=selected_action,
            rationale=rationale,
            metrics_snapshot=self._metrics_snapshot(),
        )
