from __future__ import annotations

from enum import Enum


class NodeType(str, Enum):
    SERVER = "server"
    DATABASE = "database"
    IOT = "iot"
    ENDPOINT = "endpoint"


class CompromisedState(str, Enum):
    NONE = "none"
    USER = "user"
    PRIVILEGED = "privileged"


class DetectionState(str, Enum):
    UNDETECTED = "undetected"
    SUSPECTED = "suspected"
    CONFIRMED = "confirmed"
