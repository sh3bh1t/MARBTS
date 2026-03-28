from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from hart.enums import ActorType


@dataclass(frozen=True)
class PolicyScoreBreakdown:
    total_score: float
    components: Mapping[str, float]


@dataclass(frozen=True)
class DecisionRationale:
    policy_name: str
    summary: str
    predicted_effect: str
    confidence: float
    utility_estimate: float
    score_breakdown: PolicyScoreBreakdown
    tie_breaker: str


@dataclass(frozen=True)
class ActionCandidate:
    action_type: str
    targets: tuple[str, ...]
    score: PolicyScoreBreakdown
    confidence: float
    predicted_effect: str


@dataclass(frozen=True)
class PolicyContext:
    actor: ActorType
    timestep: int
    scenario_id: str
    seed: int
    compromised_nodes: int
    policy_metrics: Mapping[str, int]


@dataclass(frozen=True)
class PolicyMetricsSnapshot:
    policy_name: str
    actions_selected: int
    action_type_counts: Mapping[str, int] = field(default_factory=dict)