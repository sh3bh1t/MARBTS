from __future__ import annotations

from environment.legal_actions import LegalAction
from hart.enums import ActionType, ActorType
from hart.models import AdaptivePolicyConfig, DeceptionEvent, PolicyContext


_DECOY_ACTIONS: dict[ActorType, set[ActionType]] = {
    ActorType.RED: {ActionType.SCAN},
    ActorType.BLUE: {ActionType.MONITOR, ActionType.BLOCK},
}
_BLUFF_ACTIONS: dict[ActorType, set[ActionType]] = {
    ActorType.RED: {ActionType.LATERAL_MOVE, ActionType.ESCALATE},
    ActorType.BLUE: {ActionType.ISOLATE, ActionType.PATCH},
}


def _compute_tactic_score(*, tactic: str, actor: ActorType, context: PolicyContext, config: AdaptivePolicyConfig) -> float:
    pressure = min(float(context.compromised_nodes), 10.0)
    if actor == ActorType.BLUE:
        base = 0.85 + pressure * 0.22 if tactic == "decoy" else 0.65 + pressure * 0.18
    else:
        base = 0.55 + pressure * 0.12 if tactic == "decoy" else 0.75 + pressure * 0.16

    score = base * config.deception_bias
    if config.reduced_observability:
        score *= 0.85
    return round(score, 3)


def evaluate_deception_hook(
    *,
    actor: ActorType,
    action: LegalAction,
    context: PolicyContext,
    config: AdaptivePolicyConfig,
) -> tuple[float, DeceptionEvent | None]:
    tactic: str | None = None

    if config.enable_decoy and action.action_type in _DECOY_ACTIONS.get(actor, set()):
        tactic = "decoy"
    elif config.enable_bluff and action.action_type in _BLUFF_ACTIONS.get(actor, set()):
        tactic = "bluff"

    if tactic is None:
        return 0.0, None

    bonus = _compute_tactic_score(
        tactic=tactic,
        actor=actor,
        context=context,
        config=config,
    )
    confidence = round(min(0.95, 0.55 + bonus / 10.0), 3)
    trigger = f"{tactic}_hook:{actor.value}:compromised_nodes={context.compromised_nodes}"

    event = DeceptionEvent(
        tactic=tactic,
        actor=actor.value,
        action_type=action.action_type.value,
        timestep=context.timestep,
        targets=action.targets,
        trigger=trigger,
        expected_shift=bonus,
        confidence=confidence,
    )
    return bonus, event
