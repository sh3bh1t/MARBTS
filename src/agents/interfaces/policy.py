from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from environment.legal_actions import LegalAction
from hart.enums import ActorType
from hart.models import DecisionRationale, PolicyContext, PolicyMetricsSnapshot


@dataclass(frozen=True)
class PolicyDecision:
    action: LegalAction
    rationale: DecisionRationale
    metrics_snapshot: PolicyMetricsSnapshot


class AgentPolicy(Protocol):
    name: str
    actor: ActorType

    def select_action(self, context: PolicyContext, legal_actions: tuple[LegalAction, ...]) -> PolicyDecision:
        ...


class PolicyRegistry:
    def __init__(self) -> None:
        self._policies: dict[ActorType, AgentPolicy] = {}

    def register(self, policy: AgentPolicy) -> None:
        self._policies[policy.actor] = policy

    def get(self, actor: ActorType) -> AgentPolicy:
        if actor not in self._policies:
            raise KeyError(f"no policy registered for actor '{actor.value}'")
        return self._policies[actor]

    def has(self, actor: ActorType) -> bool:
        return actor in self._policies