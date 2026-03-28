from __future__ import annotations

from collections import defaultdict

from agents.interfaces.policy import PolicyDecision
from environment.legal_actions import LegalAction
from hart.enums import ActionType, ActorType
from hart.models import DecisionRationale, PolicyContext, PolicyMetricsSnapshot, PolicyScoreBreakdown


class RuleBasedRedPolicy:
    name = "rule_based_red_v1"
    actor = ActorType.RED

    def __init__(self) -> None:
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)

    def _base_priority(self, action: LegalAction) -> float:
        priorities = {
            ActionType.SCAN: 80.0,
            ActionType.EXPLOIT: 70.0,
            ActionType.LATERAL_MOVE: 60.0,
            ActionType.ESCALATE: 50.0,
        }
        return priorities.get(action.action_type, 0.0)

    def _score_components(self, action: LegalAction, context: PolicyContext) -> dict[str, float]:
        compromised_pressure = float(context.compromised_nodes)
        components: dict[str, float] = {
            "phase_priority": self._base_priority(action),
            "expected_gain": 0.0,
            "path_expansion": 0.0,
            "escalation_potential": 0.0,
            "risk_pressure": compromised_pressure * 0.25,
        }

        if action.action_type == ActionType.SCAN:
            components["expected_gain"] = 6.0
            components["path_expansion"] = 2.0
        elif action.action_type == ActionType.EXPLOIT:
            components["expected_gain"] = 9.0
            components["escalation_potential"] = 3.0
        elif action.action_type == ActionType.LATERAL_MOVE:
            components["expected_gain"] = 7.0
            components["path_expansion"] = 5.0
        elif action.action_type == ActionType.ESCALATE:
            components["expected_gain"] = 5.0
            components["escalation_potential"] = 8.0

        return components

    def _predict_effect(self, action: LegalAction) -> str:
        if action.action_type == ActionType.SCAN:
            return "increase environmental visibility for next offensive decisions"
        if action.action_type == ActionType.EXPLOIT:
            return "advance compromise state on vulnerable target"
        if action.action_type == ActionType.LATERAL_MOVE:
            return "expand foothold into adjacent network segment"
        if action.action_type == ActionType.ESCALATE:
            return "increase privilege level on already compromised host"
        return "maintain offensive pressure"

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