from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from utils.runtime_presets import load_experiment_preset, load_seed_bundle


def test_load_seed_bundle_happy_path() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_file = Path(temp_dir) / "bundle.json"
        bundle_file.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.seed_bundle.v1",
                    "bundle_id": "smoke",
                    "description": "seed smoke",
                    "seeds": [11, 12, 13],
                }
            ),
            encoding="utf-8",
        )

        bundle = load_seed_bundle(bundle_file)

        assert bundle.bundle_id == "smoke"
        assert bundle.seeds == (11, 12, 13)


def test_load_experiment_preset_uses_relative_seed_bundle() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        seed_bundle = root / "seeds.json"
        preset = root / "preset.json"

        seed_bundle.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.seed_bundle.v1",
                    "bundle_id": "from-bundle",
                    "seeds": [9001, 9002],
                }
            ),
            encoding="utf-8",
        )
        preset.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.runtime_preset.v1",
                    "preset_id": "preset-a",
                    "seed_bundle": "seeds.json",
                    "runtime": {
                        "scenario_path": "scenarios/baselines/rule_baseline.json",
                        "horizon": 5,
                    },
                }
            ),
            encoding="utf-8",
        )

        loaded = load_experiment_preset(preset)

        assert loaded.preset_id == "preset-a"
        assert loaded.runtime.scenario_path == "scenarios/baselines/rule_baseline.json"
        assert loaded.runtime.horizon == 5
        assert loaded.runtime.seeds == (9001, 9002)
        assert loaded.seed_bundle == "from-bundle"


def test_runtime_seeds_override_seed_bundle() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        seed_bundle = root / "seeds.json"
        preset = root / "preset.json"

        seed_bundle.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.seed_bundle.v1",
                    "bundle_id": "bundle",
                    "seeds": [1, 2],
                }
            ),
            encoding="utf-8",
        )
        preset.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.runtime_preset.v1",
                    "preset_id": "preset-b",
                    "seed_bundle": "seeds.json",
                    "runtime": {
                        "seeds": [42],
                    },
                }
            ),
            encoding="utf-8",
        )

        loaded = load_experiment_preset(preset)
        assert loaded.runtime.seeds == (42,)


def test_load_seed_bundle_rejects_empty_seed_list() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        bundle_file = Path(temp_dir) / "bundle.json"
        bundle_file.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.seed_bundle.v1",
                    "bundle_id": "empty",
                    "seeds": [],
                }
            ),
            encoding="utf-8",
        )

        with pytest.raises(ValueError, match="cannot be empty"):
            load_seed_bundle(bundle_file)
