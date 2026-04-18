from __future__ import annotations

from enum import Enum


class ActorType(str, Enum):
    RED = "red"
    BLUE = "blue"


class ActionType(str, Enum):
    SCAN = "scan"
    EXPLOIT = "exploit"
    LATERAL_MOVE = "lateral_move"
    ESCALATE = "escalate"
    MONITOR = "monitor"
    PATCH = "patch"
    BLOCK = "block"
    ISOLATE = "isolate"
    DECOY = "decoy"
    FEINT = "feint"


def parse_actor(actor: str | ActorType) -> ActorType:
    if isinstance(actor, ActorType):
        return actor
    return ActorType(actor)
