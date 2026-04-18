from __future__ import annotations

from collections import defaultdict
import os
from typing import Protocol

from openai import OpenAI
from pydantic import BaseModel, Field

from agents.adaptive.ablation import apply_observability_filter, effective_planning_depth
from agents.adaptive.planning import AdaptivePlanningPolicy
from agents.blue.rule_based import RuleBasedBluePolicy
from agents.interfaces.policy import PolicyDecision
from agents.red.rule_based import RuleBasedRedPolicy
from environment.legal_actions import LegalAction
from hart.enums import ActorType
from hart.models import AdaptivePolicyConfig, DecisionRationale, PolicyContext, PolicyMetricsSnapshot, PolicyScoreBreakdown


class _LLMDecisionPayload(BaseModel):
    action_type: str = Field(description="The selected legal action type.")
    targets: list[str] = Field(description="Ordered list of action targets.")
    summary: str = Field(description="Short explanation for why this action is selected.")
    predicted_effect: str = Field(description="Expected simulated effect of the chosen action.")
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in the selected action.")
    utility_estimate: float = Field(description="Relative utility estimate for the selected action.")


class ResponsesAPIClient(Protocol):
    class _Responses(Protocol):
        def parse(self, **kwargs): ...

    responses: _Responses


class OpenAIAdaptivePolicy:
    def __init__(
        self,
        actor: ActorType,
        config: AdaptivePolicyConfig | None = None,
        *,
        client: ResponsesAPIClient | None = None,
    ) -> None:
        self.actor = actor
        self.config = config or AdaptivePolicyConfig(backend="openai")
        self.name = f"openai_adaptive_{actor.value}_v1"
        self._actions_selected = 0
        self._action_type_counts: dict[str, int] = defaultdict(int)
        self._client = client
        self._fallback_policy = self._build_fallback_policy()

    def _build_fallback_policy(self):
        if self.config.fallback_backend == "planning":
            fallback_config = AdaptivePolicyConfig(
                planning_depth=self.config.planning_depth,
                planning_mode=self.config.planning_mode,
                opponent_policy_name=self.config.opponent_policy_name,
                backend="planning",
                feature_flags=dict(self.config.feature_flags),
            )
            return AdaptivePlanningPolicy(self.actor, fallback_config)

        if self.actor == ActorType.RED:
            return RuleBasedRedPolicy()
        return RuleBasedBluePolicy()

    def _metrics_snapshot(self) -> PolicyMetricsSnapshot:
        return PolicyMetricsSnapshot(
            policy_name=self.name,
            actions_selected=self._actions_selected,
            action_type_counts=dict(sorted(self._action_type_counts.items())),
        )

    def _get_client(self) -> ResponsesAPIClient:
        if self._client is not None:
            return self._client

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is required for the OpenAI adaptive policy")

        client_kwargs: dict[str, str] = {"api_key": api_key}
        if self.config.api_base_url:
            client_kwargs["base_url"] = self.config.api_base_url

        self._client = OpenAI(**client_kwargs)
        return self._client

    def _system_prompt(self, legal_actions: tuple[LegalAction, ...]) -> str:
        formatted_actions = []
        for index, action in enumerate(legal_actions):
            formatted_actions.append(
                f"{index}: action_type={action.action_type.value}; targets={list(action.targets)}; rationale_hint={action.rationale_hint}"
            )

        return (
            "You are selecting the next action for a sandboxed synthetic cyber-defense simulation. "
            "Only choose one of the provided legal actions exactly as listed. "
            "Do not invent actions, tools, targets, exploits, or external operations. "
            "Respond using the requested structured schema only.\n"
            f"Actor: {self.actor.value}\n"
            "Legal actions:\n"
            + "\n".join(formatted_actions)
        )

    def _user_prompt(self, context: PolicyContext) -> str:
        visible_snapshot = apply_observability_filter(context.state_snapshot, self.config)
        return (
            f"Scenario: {context.scenario_id}\n"
            f"Timestep: {context.timestep}\n"
            f"Seed: {context.seed}\n"
            f"Compromised nodes: {context.compromised_nodes}\n"
            f"Policy metrics: {dict(context.policy_metrics)}\n"
            f"Planning depth request: {effective_planning_depth(self.config)}\n"
            f"State snapshot: {visible_snapshot}\n"
            "Select the best legal action for the current actor and explain the expected synthetic impact."
        )

    def _resolve_legal_action(
        self,
        selection: _LLMDecisionPayload,
        legal_actions: tuple[LegalAction, ...],
    ) -> LegalAction:
        for action in legal_actions:
            if action.action_type.value == selection.action_type and action.targets == tuple(selection.targets):
                return action
        raise ValueError(
            f"model selected illegal action action_type={selection.action_type!r} targets={selection.targets!r}"
        )

    def _fallback_decision(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...], reason: str) -> PolicyDecision:
        if self.config.feature_flags.get("require_live_llm", False):
            raise RuntimeError(reason)

        fallback_decision = self._fallback_policy.select_action(context, legal_actions)
        fallback_rationale = fallback_decision.rationale
        trace = dict(fallback_rationale.trace)
        trace["openai_fallback_reason"] = reason
        trace["requested_backend"] = self.config.backend
        updated_rationale = DecisionRationale(
            policy_name=self.name,
            summary=f"{fallback_rationale.summary} (fallback after OpenAI decision failure)",
            predicted_effect=fallback_rationale.predicted_effect,
            confidence=fallback_rationale.confidence,
            utility_estimate=fallback_rationale.utility_estimate,
            score_breakdown=fallback_rationale.score_breakdown,
            tie_breaker=fallback_rationale.tie_breaker,
            trace=trace,
        )
        return PolicyDecision(
            action=fallback_decision.action,
            rationale=updated_rationale,
            metrics_snapshot=self._metrics_snapshot_for_action(fallback_decision.action.action_type.value),
        )

    def _metrics_snapshot_for_action(self, action_type: str) -> PolicyMetricsSnapshot:
        self._actions_selected += 1
        self._action_type_counts[action_type] += 1
        return self._metrics_snapshot()

    def select_action(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...]) -> PolicyDecision:
        if not legal_actions:
            raise ValueError("legal_actions cannot be empty")

        try:
            client = self._get_client()
            request_kwargs = {
                "model": self.config.model_name,
                "input": [
                    {"role": "system", "content": self._system_prompt(legal_actions)},
                    {"role": "user", "content": self._user_prompt(context)},
                ],
                "text_format": _LLMDecisionPayload,
                "reasoning": {"effort": self.config.reasoning_effort},
                "max_output_tokens": self.config.max_output_tokens,
            }
            if self.config.temperature is not None:
                request_kwargs["temperature"] = self.config.temperature

            response = client.responses.parse(
                **request_kwargs,
            )
            parsed = response.output_parsed
            if parsed is None:
                raise ValueError("OpenAI response did not include parsed structured output")
            selected_action = self._resolve_legal_action(parsed, legal_actions)
        except Exception as exc:
            return self._fallback_decision(context, legal_actions, str(exc))

        metrics_snapshot = self._metrics_snapshot_for_action(selected_action.action_type.value)
        score_breakdown = PolicyScoreBreakdown(
            total_score=float(parsed.utility_estimate),
            components={
                "llm_utility_estimate": float(parsed.utility_estimate),
                "reported_confidence": float(parsed.confidence),
                "planning_depth": float(effective_planning_depth(self.config)),
            },
        )
        rationale = DecisionRationale(
            policy_name=self.name,
            summary=parsed.summary,
            predicted_effect=parsed.predicted_effect,
            confidence=float(parsed.confidence),
            utility_estimate=float(parsed.utility_estimate),
            score_breakdown=score_breakdown,
            tie_breaker="OpenAI structured response followed by legal-action validation",
            trace={
                "backend": "openai_responses",
                "model_name": self.config.model_name,
                "reasoning_effort": self.config.reasoning_effort,
                "selected_action": selected_action.action_type.value,
                "selected_targets": list(selected_action.targets),
                "fallback_backend": self.config.fallback_backend,
                "state_snapshot_present": bool(context.state_snapshot),
                "feature_flags": dict(self.config.feature_flags),
                "planning_depth": effective_planning_depth(self.config),
            },
        )
        return PolicyDecision(
            action=selected_action,
            rationale=rationale,
            metrics_snapshot=metrics_snapshot,
        )
