from __future__ import annotations

from collections import defaultdict

from agents.interfaces.policy import PolicyDecision
from environment.legal_actions import LegalAction
from hart.enums import ActionType, ActorType
from hart.models import (
    AdaptivePolicyConfig,
    DecisionRationale,
    ModelInferenceRecord,
    PlanningTrace,
    PolicyContext,
    PolicyMetricsSnapshot,
    PolicyScoreBreakdown,
    ValueEstimate,
)


_RED_ALLOWED_ACTIONS = {
    ActionType.SCAN,
    ActionType.EXPLOIT,
    ActionType.LATERAL_MOVE,
    ActionType.ESCALATE,
}
_BLUE_ALLOWED_ACTIONS = {
    ActionType.MONITOR,
    ActionType.PATCH,
    ActionType.BLOCK,
    ActionType.ISOLATE,
}

_ACTION_ARITY = {
    ActionType.SCAN: 1,
    ActionType.EXPLOIT: 1,
    ActionType.LATERAL_MOVE: 2,
    ActionType.ESCALATE: 1,
    ActionType.MONITOR: 1,
    ActionType.PATCH: 1,
    ActionType.BLOCK: 2,
    ActionType.ISOLATE: 1,
}


class AdaptivePlanningPolicy:
    def __init__(self, actor: ActorType, config: AdaptivePolicyConfig | None = None) -> None:
        self.actor = actor
        self.config = config or AdaptivePolicyConfig()
        self.name = f"adaptive_planning_{actor.value}_v1"
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)

    def _allowed_actions(self) -> set[ActionType]:
        if self.actor == ActorType.RED:
            return _RED_ALLOWED_ACTIONS
        return _BLUE_ALLOWED_ACTIONS

    def _is_safe_legal_action(self, action: LegalAction) -> bool:
        if action.actor != self.actor:
            return False
        if action.action_type not in self._allowed_actions():
            return False
        expected_arity = _ACTION_ARITY.get(action.action_type)
        if expected_arity is None:
            return False
        return len(action.targets) == expected_arity

    def _base_utility(self, action: LegalAction) -> float:
        if self.actor == ActorType.RED:
            red_utility = {
                ActionType.SCAN: 3.2,
                ActionType.EXPLOIT: 7.8,
                ActionType.LATERAL_MOVE: 6.9,
                ActionType.ESCALATE: 6.1,
            }
            return red_utility.get(action.action_type, 0.0)

        blue_utility = {
            ActionType.MONITOR: 2.8,
            ActionType.PATCH: 6.4,
            ActionType.BLOCK: 7.2,
            ActionType.ISOLATE: 7.5,
        }
        return blue_utility.get(action.action_type, 0.0)

    def _project_compromised_delta(self, action: LegalAction) -> float:
        if self.actor == ActorType.RED:
            if action.action_type in {ActionType.EXPLOIT, ActionType.LATERAL_MOVE}:
                return 1.0
            if action.action_type == ActionType.ESCALATE:
                return 0.4
            return 0.2

        if action.action_type == ActionType.ISOLATE:
            return -1.0
        if action.action_type == ActionType.BLOCK:
            return -0.8
        if action.action_type == ActionType.PATCH:
            return -0.6
        return -0.2

    def _threat_or_gain_pressure(self, compromised_nodes: float) -> float:
        if self.actor == ActorType.RED:
            return compromised_nodes * 0.45
        return compromised_nodes * 1.15

    def _project_plan(self, action: LegalAction, context: PolicyContext) -> PlanningTrace:
        projected_compromised = float(context.compromised_nodes)
        value_estimates: list[ValueEstimate] = []
        cumulative_utility = 0.0

        for step in range(self.config.planning_horizon):
            pressure = self._threat_or_gain_pressure(projected_compromised)
            immediate = self._base_utility(action) + pressure
            discounted = immediate * (self.config.discount_factor ** step)

            value_estimates.append(
                ValueEstimate(
                    step=step,
                    immediate_utility=round(immediate, 3),
                    discounted_utility=round(discounted, 3),
                    projected_compromised_nodes=round(projected_compromised, 3),
                )
            )

            cumulative_utility += discounted
            projected_compromised += self._project_compromised_delta(action)
            projected_compromised = max(
                0.0,
                min(projected_compromised, float(self.config.max_compromised_projection)),
            )

        return PlanningTrace(
            action_type=action.action_type.value,
            targets=action.targets,
            horizon=self.config.planning_horizon,
            cumulative_utility=round(cumulative_utility, 3),
            value_estimates=tuple(value_estimates),
        )

    def _exploration_bonus(self, action: LegalAction) -> float:
        prior_selections = self._action_type_counts[action.action_type.value]
        return round(self.config.exploration_bias / (1 + prior_selections), 3)

    def _predict_effect(self, action: LegalAction) -> str:
        predictions = {
            ActionType.SCAN: "increase uncertainty reduction before offensive commitment",
            ActionType.EXPLOIT: "increase probability of initial or expanded compromise",
            ActionType.LATERAL_MOVE: "extend attacker reach into adjacent network segments",
            ActionType.ESCALATE: "raise privilege depth on established foothold",
            ActionType.MONITOR: "improve defender observability for follow-up containment",
            ActionType.PATCH: "reduce vulnerable surface and compromise persistence",
            ActionType.BLOCK: "break attack-path connectivity and delay propagation",
            ActionType.ISOLATE: "contain blast radius by severing node traffic paths",
        }
        return predictions.get(action.action_type, "maintain adaptive posture")

    def _confidence(self, score: float) -> float:
        bounded = max(0.0, min(score, 100.0))
        return round(0.35 + (bounded / 100.0) * 0.65, 3)

    def _metrics_snapshot(self) -> PolicyMetricsSnapshot:
        return PolicyMetricsSnapshot(
            policy_name=self.name,
            actions_selected=self._actions_selected,
            action_type_counts=dict(sorted(self._action_type_counts.items())),
        )

    def select_action(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...]) -> PolicyDecision:
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")

        safe_actions = tuple(action for action in legal_actions if self._is_safe_legal_action(action))
        if not safe_actions:
            raise ValueError("no safe legal actions available for adaptive policy")

        candidates: list[
            tuple[
                float,
                str,
                tuple[str, ...],
                LegalAction,
                dict[str, float],
                PlanningTrace,
                ModelInferenceRecord,
            ]
        ] = []

        for action in safe_actions:
            planning_trace = self._project_plan(action, context)
            exploration_bonus = self._exploration_bonus(action)
            total_score = round(planning_trace.cumulative_utility + exploration_bonus, 3)
            components = {
                "planning_utility": planning_trace.cumulative_utility,
                "exploration_bonus": exploration_bonus,
                "horizon": float(self.config.planning_horizon),
                "safety_passed": 1.0,
            }
            inference_record = ModelInferenceRecord(
                model_family="heuristic_planner",
                model_name=self.name,
                deterministic=True,
                input_features={
                    "actor": self.actor.value,
                    "timestep": context.timestep,
                    "compromised_nodes": context.compromised_nodes,
                    "action_type": action.action_type.value,
                },
                output_action=action.action_type.value,
                output_utility=total_score,
            )
            candidates.append(
                (
                    total_score,
                    action.action_type.value,
                    action.targets,
                    action,
                    components,
                    planning_trace,
                    inference_record,
                )
            )

        candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
        selected_score, _, _, selected_action, components, planning_trace, inference_record = candidates[0]

        self._actions_selected += 1
        self._action_type_counts[selected_action.action_type.value] += 1

        rationale = DecisionRationale(
            policy_name=self.name,
            summary=f"selected {selected_action.action_type.value} using bounded adaptive planning",
            predicted_effect=self._predict_effect(selected_action),
            confidence=self._confidence(selected_score),
            utility_estimate=selected_score,
            score_breakdown=PolicyScoreBreakdown(total_score=selected_score, components=components),
            tie_breaker="(-score, action_type, targets)",
            planning_trace=planning_trace,
            inference_record=inference_record,
        )

        return PolicyDecision(
            action=selected_action,
            rationale=rationale,
            metrics_snapshot=self._metrics_snapshot(),
        )