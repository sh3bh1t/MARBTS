from __future__ import annotations

import pytest

from scripts.run_multi_seed_report import _parse_seeds


def test_parse_seeds_happy_path() -> None:
    assert _parse_seeds("1,2,3") == [1, 2, 3]


def test_parse_seeds_ignores_spaces() -> None:
    assert _parse_seeds(" 10, 20 ,30 ") == [10, 20, 30]


def test_parse_seeds_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one"):
        _parse_seeds("  ")


def test_parse_seeds_rejects_non_integer() -> None:
    with pytest.raises(ValueError, match="comma-separated list of integers"):
        _parse_seeds("1,two,3")