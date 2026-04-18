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
    trace: Mapping[str, object] = field(default_factory=dict)


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
    state_snapshot: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class PolicyMetricsSnapshot:
    policy_name: str
    actions_selected: int
    action_type_counts: Mapping[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class AdaptivePolicyConfig:
    planning_depth: int = 2
    planning_mode: str = "bounded_rollout"
    opponent_policy_name: str = "rule_based"
    backend: str = "planning"
    model_name: str = "gpt-5-mini"
    reasoning_effort: str = "low"
    api_base_url: str | None = None
    temperature: float | None = None
    max_output_tokens: int = 400
    fallback_backend: str = "planning"
    feature_flags: Mapping[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class AblationConfig:
    no_planning: bool = False
    reduced_observability: bool = False
    no_decoy: bool = True


@dataclass(frozen=True)
class ExperimentCondition:
    condition_id: str
    red_policy: str
    blue_policy: str
    adaptive_config: AdaptivePolicyConfig | None = None
    ablation: AblationConfig = field(default_factory=AblationConfig)


@dataclass(frozen=True)
class ComparisonMetricBundle:
    condition_id: str
    seed_count: int
    mean_final_compromised_nodes: float
    min_final_compromised_nodes: int
    max_final_compromised_nodes: int


@dataclass(frozen=True)
class ValueEstimate:
    action_type: str
    targets: tuple[str, ...]
    utility: float
    confidence: float
    summary: str


@dataclass(frozen=True)
class PlanningTrace:
    planning_depth: int
    selected_action: str
    candidate_values: tuple[ValueEstimate, ...]
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class ModelInferenceRecord:
    policy_name: str
    deterministic: bool
    trace: PlanningTrace
