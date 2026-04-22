from __future__ import annotations

import pytest

from scripts.run_policy_experiment_matrix import _parse_scenario_batch


def test_parse_scenario_batch_happy_path() -> None:
    assert _parse_scenario_batch("scenarios/baselines/rule_baseline.json,scenarios/library/containment_stress.json") == [
        "scenarios/baselines/rule_baseline.json",
        "scenarios/library/containment_stress.json",
    ]


def test_parse_scenario_batch_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one scenario path"):
        _parse_scenario_batch("   ")