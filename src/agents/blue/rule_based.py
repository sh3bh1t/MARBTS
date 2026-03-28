from __future__ import annotations

from collections import defaultdict

from agents.interfaces.policy import PolicyDecision
from environment.legal_actions import LegalAction
from hart.enums import ActionType, ActorType
from hart.models import DecisionRationale, PolicyContext, PolicyMetricsSnapshot, PolicyScoreBreakdown


class RuleBasedBluePolicy:
    name = "rule_based_blue_v1"
    actor = ActorType.BLUE

    def __init__(self) -> None:
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)

    def _base_priority(self, action: LegalAction) -> float:
        priorities = {
            ActionType.MONITOR: 80.0,
            ActionType.PATCH: 70.0,
            ActionType.BLOCK: 60.0,
            ActionType.ISOLATE: 50.0,
        }
        return priorities.get(action.action_type, 0.0)

    def _score_components(self, action: LegalAction, context: PolicyContext) -> dict[str, float]:
        threat_pressure = float(context.compromised_nodes)
        components: dict[str, float] = {
            "phase_priority": self._base_priority(action),
            "threat_suppression": 0.0,
            "containment_urgency": 0.0,
            "resilience_impact": 0.0,
            "threat_pressure": threat_pressure * 1.2,
            "emergency_containment": 0.0,
            "monitoring_penalty": 0.0,
        }

        if action.action_type == ActionType.MONITOR:
            components["threat_suppression"] = 6.0
            components["resilience_impact"] = 3.0
            components["monitoring_penalty"] = -threat_pressure * 10.0
        elif action.action_type == ActionType.PATCH:
            components["threat_suppression"] = 8.0
            components["resilience_impact"] = 6.0
        elif action.action_type == ActionType.BLOCK:
            components["containment_urgency"] = 8.0 + threat_pressure * 1.4
            components["threat_suppression"] = 6.0 + threat_pressure * 1.1
            components["resilience_impact"] = 3.0
            components["emergency_containment"] = threat_pressure * 12.0
        elif action.action_type == ActionType.ISOLATE:
            components["containment_urgency"] = 9.0 + threat_pressure * 1.7
            components["threat_suppression"] = 7.0 + threat_pressure * 1.2
            components["resilience_impact"] = 2.0
            components["emergency_containment"] = threat_pressure * 13.0

        return components

    def _predict_effect(self, action: LegalAction) -> str:
        if action.action_type == ActionType.MONITOR:
            return "increase defender observability for risk-informed controls"
        if action.action_type == ActionType.PATCH:
            return "reduce vulnerabilities and remove compromise persistence"
        if action.action_type == ActionType.BLOCK:
            return "disrupt attack path connectivity between nodes"
        if action.action_type == ActionType.ISOLATE:
            return "contain suspected compromise blast radius"
        return "maintain defensive posture"

    def _confidence(self, total_score: float) -> float:
        bounded = max(0.0, min(total_score, 100.0))
        return round(0.4 + (bounded / 100.0) * 0.6, 3)

    def _metrics_snapshot(self) -> PolicyMetricsSnapshot:
        return PolicyMetricsSnapshot(
            policy_name=self.name,
            actions_selected=self._actions_selected,
            action_type_counts=dict(sorted(self._action_type_counts.items())),
        )

    def select_action(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...]) -> PolicyDecision:
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")

        scored: list[tuple[float, str, tuple[str, ...], LegalAction, dict[str, float]]] = []
        for action in legal_actions:
            components = self._score_components(action, context)
            total_score = sum(components.values())
            scored.append((total_score, action.action_type.value, action.targets, action, components))

        scored.sort(key=lambda item: (-item[0], item[1], item[2]))
        selected_score, _, _, selected_action, components = scored[0]

        self._actions_selected += 1
        self._action_type_counts[selected_action.action_type.value] += 1

        score_breakdown = PolicyScoreBreakdown(total_score=selected_score, components=components)
        rationale = DecisionRationale(
            policy_name=self.name,
            summary=f"selected {selected_action.action_type.value} via deterministic heuristic ranking",
            predicted_effect=self._predict_effect(selected_action),
            confidence=self._confidence(selected_score),
            utility_estimate=round(selected_score / 10.0, 3),
            score_breakdown=score_breakdown,
            tie_breaker="(-score, action_type, targets)",
        )

        return PolicyDecision(
            action=selected_action,
            rationale=rationale,
            metrics_snapshot=self._metrics_snapshot(),
        )