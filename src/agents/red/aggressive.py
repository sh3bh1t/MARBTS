from __future__ import annotations

from collections import defaultdict

from agents.interfaces.policy import PolicyDecision
from environment.legal_actions import LegalAction
from hart.enums import ActionType, ActorType
from hart.models import DecisionRationale, PolicyContext, PolicyMetricsSnapshot, PolicyScoreBreakdown


class AggressiveRedPolicy:
    name = "aggressive_red_v1"
    actor = ActorType.RED

    def __init__(self) -> None:
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)

    def _base_priority(self, action: LegalAction) -> float:
        priorities = {
            ActionType.EXPLOIT: 95.0,
            ActionType.LATERAL_MOVE: 88.0,
            ActionType.ESCALATE: 82.0,
            ActionType.SCAN: 60.0,
        }
        return priorities.get(action.action_type, 0.0)

    def _score_components(self, action: LegalAction, context: PolicyContext) -> dict[str, float]:
        scan_count = float(context.policy_metrics.get(ActionType.SCAN.value, 0))
        components: dict[str, float] = {
            "phase_priority": self._base_priority(action),
            "expected_gain": 0.0,
            "target_pressure": float(context.compromised_nodes) * 0.5,
            "repeat_scan_penalty": 0.0,
        }

        if action.action_type == ActionType.EXPLOIT:
            components["expected_gain"] = 14.0
        elif action.action_type == ActionType.LATERAL_MOVE:
            components["expected_gain"] = 11.0
        elif action.action_type == ActionType.ESCALATE:
            components["expected_gain"] = 9.0
        elif action.action_type == ActionType.SCAN:
            components["expected_gain"] = 5.0
            components["repeat_scan_penalty"] = -(scan_count * 12.0)

        return components

    def _predict_effect(self, action: LegalAction) -> str:
        if action.action_type == ActionType.EXPLOIT:
            return "attempt immediate compromise on a vulnerable target"
        if action.action_type == ActionType.LATERAL_MOVE:
            return "push compromise into a new adjacent node"
        if action.action_type == ActionType.ESCALATE:
            return "raise privileges on the current foothold"
        return "collect limited reconnaissance before the next attack"

    def _confidence(self, total_score: float) -> float:
        bounded = max(0.0, min(total_score, 100.0))
        return round(0.45 + (bounded / 100.0) * 0.5, 3)

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

        rationale = DecisionRationale(
            policy_name=self.name,
            summary=f"selected {selected_action.action_type.value} via aggressive offensive heuristic ranking",
            predicted_effect=self._predict_effect(selected_action),
            confidence=self._confidence(selected_score),
            utility_estimate=round(selected_score / 10.0, 3),
            score_breakdown=PolicyScoreBreakdown(total_score=selected_score, components=components),
            tie_breaker="(-score, action_type, targets)",
        )
        return PolicyDecision(
            action=selected_action,
            rationale=rationale,
            metrics_snapshot=self._metrics_snapshot(),
        )
