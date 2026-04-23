from __future__ import annotations

from enum import Enum


class TopologyComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


class VulnerabilityDensity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DefensePosture(str, Enum):
    PERMISSIVE = "permissive"
    BALANCED = "balanced"
    HARDENED = "hardened"