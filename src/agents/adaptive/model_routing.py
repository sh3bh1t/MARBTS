from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from environment.legal_actions import LegalAction
from hart.models import AdaptivePolicyConfig, ModelRoutingConfig, PolicyContext


@dataclass(frozen=True)
class RoutingDecision:
    action_type: str
    targets: tuple[str, ...]
    utility: float
    rationale: str
    provider: str
    deterministic: bool
    raw_payload: dict[str, Any]


class ModelRoutingError(RuntimeError):
    pass


class BaseModelRouter:
    def route(self, *, context: PolicyContext, legal_actions: tuple[LegalAction, ...], config: AdaptivePolicyConfig) -> RoutingDecision:
        raise NotImplementedError


class HeuristicModelRouter(BaseModelRouter):
    def route(self, *, context: PolicyContext, legal_actions: tuple[LegalAction, ...], config: AdaptivePolicyConfig) -> RoutingDecision:
        if not legal_actions:
            raise ModelRoutingError("legal_actions cannot be empty")

        selected = legal_actions[0]
        rationale = f"heuristic fallback selected {selected.action_type.value}"
        utility = float(context.compromised_nodes) * 0.1
        return RoutingDecision(
            action_type=selected.action_type.value,
            targets=selected.targets,
            utility=round(utility, 3),
            rationale=rationale,
            provider="heuristic",
            deterministic=True,
            raw_payload={"fallback": True, "provider": "heuristic"},
        )


class RemoteModelRouter(BaseModelRouter):
    def __init__(self, routing_config: ModelRoutingConfig) -> None:
        self.routing_config = routing_config

    def route(self, *, context: PolicyContext, legal_actions: tuple[LegalAction, ...], config: AdaptivePolicyConfig) -> RoutingDecision:
        if not self.routing_config.enabled:
            raise ModelRoutingError("remote model routing is disabled")
        if not legal_actions:
            raise ModelRoutingError("legal_actions cannot be empty")

        selected = legal_actions[0]
        rationale = (
            f"provider={self.routing_config.provider} model={self.routing_config.model_name or 'unspecified'} "
            f"selected {selected.action_type.value} as legal default"
        )
        utility = float(context.compromised_nodes) * 0.2
        return RoutingDecision(
            action_type=selected.action_type.value,
            targets=selected.targets,
            utility=round(utility, 3),
            rationale=rationale,
            provider=self.routing_config.provider,
            deterministic=self.routing_config.temperature == 0.0,
            raw_payload={
                "provider": self.routing_config.provider,
                "model_name": self.routing_config.model_name,
                "api_base_url": self.routing_config.api_base_url,
                "api_key_env_var": self.routing_config.api_key_env_var,
                "deterministic": self.routing_config.temperature == 0.0,
                "context_actor": context.actor.value,
                "action_type": selected.action_type.value,
            },
        )


def build_model_router(config: AdaptivePolicyConfig) -> BaseModelRouter:
    if config.model_routing.enabled and config.model_routing.provider != "heuristic":
        return RemoteModelRouter(config.model_routing)
    return HeuristicModelRouter()
