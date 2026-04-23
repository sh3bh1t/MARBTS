from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from hart.enums import ActorType


@dataclass(frozen=True)
class PolicyScoreBreakdown:
    total_score: float
    components: Mapping[str, float]


@dataclass(frozen=True)
class ValueEstimate:
    step: int
    immediate_utility: float
    discounted_utility: float
    projected_compromised_nodes: float


@dataclass(frozen=True)
class PlanningTrace:
    action_type: str
    targets: tuple[str, ...]
    horizon: int
    cumulative_utility: float
    value_estimates: tuple[ValueEstimate, ...]


@dataclass(frozen=True)
class ModelInferenceRecord:
    model_family: str
    model_name: str
    deterministic: bool
    input_features: Mapping[str, Any] = field(default_factory=dict)
    output_action: str = ""
    output_utility: float = 0.0


@dataclass(frozen=True)
class DeceptionEvent:
    tactic: str
    actor: str
    action_type: str
    timestep: int
    targets: tuple[str, ...]
    trigger: str
    expected_shift: float
    confidence: float


@dataclass(frozen=True)
class AdaptivePolicyConfig:
    planning_horizon: int = 3
    discount_factor: float = 0.85
    exploration_bias: float = 0.15
    max_compromised_projection: int = 128
    reduced_observability: bool = False
    enable_decoy: bool = False
    enable_bluff: bool = False
    deception_bias: float = 1.0

    def __post_init__(self) -> None:
        if self.planning_horizon < 1:
            raise ValueError("planning_horizon must be >= 1")
        if not 0.0 < self.discount_factor <= 1.0:
            raise ValueError("discount_factor must be in the range (0.0, 1.0]")
        if self.exploration_bias < 0.0:
            raise ValueError("exploration_bias must be >= 0.0")
        if self.max_compromised_projection < 1:
            raise ValueError("max_compromised_projection must be >= 1")
        if self.deception_bias < 0.0:
            raise ValueError("deception_bias must be >= 0.0")


@dataclass(frozen=True)
class AblationConfig:
    no_planning: bool = False
    reduced_observability: bool = False


@dataclass(frozen=True)
class ExperimentCondition:
    condition_id: str
    label: str
    red_policy: str
    blue_policy: str
    seeds: tuple[int, ...]
    horizon: int
    ablation: AblationConfig = field(default_factory=AblationConfig)
    adaptive_config: AdaptivePolicyConfig | None = None
    red_ablation: AblationConfig | None = None
    blue_ablation: AblationConfig | None = None
    red_adaptive_config: AdaptivePolicyConfig | None = None
    blue_adaptive_config: AdaptivePolicyConfig | None = None


@dataclass(frozen=True)
class StressTestConfig:
    profile_id: str
    label: str
    scenario_paths: tuple[str, ...]
    seeds: tuple[int, ...]
    horizon: int
    include_ablations: bool = True
    observation_noise_proxy: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id must be a non-empty string")
        if not self.label:
            raise ValueError("label must be a non-empty string")
        if not self.scenario_paths:
            raise ValueError("scenario_paths cannot be empty")
        if not self.seeds:
            raise ValueError("seeds cannot be empty")
        if self.horizon < 1:
            raise ValueError("horizon must be >= 1")


@dataclass(frozen=True)
class ComparisonMetricBundle:
    condition_id: str
    condition_label: str
    final_compromised_mean: float
    final_compromised_stddev: float
    blue_containment_mean: float
    blue_containment_stddev: float
    deterministic_consistency_ratio: float


@dataclass(frozen=True)
class DecisionRationale:
    policy_name: str
    summary: str
    predicted_effect: str
    confidence: float
    utility_estimate: float
    score_breakdown: PolicyScoreBreakdown
    tie_breaker: str
    planning_trace: PlanningTrace | None = None
    inference_record: ModelInferenceRecord | None = None
    deception_event: DeceptionEvent | None = None


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