from __future__ import annotations

import json
import tempfile
from pathlib import Path

from marbts_cli import experiment_commands


def _write_seed_bundle(path: Path, *, bundle_id: str, seeds: list[int]) -> None:
    path.write_text(
        json.dumps(
            {
                "schema_version": "2026-04-24.seed_bundle.v1",
                "bundle_id": bundle_id,
                "seeds": seeds,
            }
        ),
        encoding="utf-8",
    )


def test_multi_seed_command_reads_preset_defaults(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        seed_bundle = root / "seeds.json"
        preset = root / "multi_seed.json"
        _write_seed_bundle(seed_bundle, bundle_id="bundle-a", seeds=[101, 202])
        preset.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.runtime_preset.v1",
                    "preset_id": "multi-seed",
                    "seed_bundle": "seeds.json",
                    "runtime": {
                        "scenario_path": "scenarios/baselines/rule_baseline.json",
                        "horizon": 7,
                        "runs_root": "artifacts/runs",
                        "metrics_root": "artifacts/metrics",
                        "reports_root": "artifacts/reports",
                    },
                }
            ),
            encoding="utf-8",
        )

        captured: dict = {}

        def _fake_run_multi_seed_report(**kwargs):
            captured.update(kwargs)
            return {
                "report_file": "artifacts/reports/fake.json",
                "report": {
                    "aggregate": {
                        "scenario_id": "rule-baseline",
                        "seed_count": len(kwargs["seeds"]),
                        "horizon": kwargs["horizon"],
                        "final_compromised_mean": 1.0,
                        "deterministic_consistency_ratio": 1.0,
                    }
                },
            }

        monkeypatch.setattr(experiment_commands, "run_multi_seed_report", _fake_run_multi_seed_report)

        experiment_commands.run_multi_seed_report_main(["--config", str(preset)])

        assert captured["scenario_path"] == Path("scenarios/baselines/rule_baseline.json")
        assert captured["seeds"] == [101, 202]
        assert captured["horizon"] == 7


def test_policy_matrix_command_allows_cli_overrides(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        seed_bundle = root / "seeds.json"
        preset = root / "policy_matrix.json"
        _write_seed_bundle(seed_bundle, bundle_id="bundle-b", seeds=[777, 888])
        preset.write_text(
            json.dumps(
                {
                    "schema_version": "2026-04-24.runtime_preset.v1",
                    "preset_id": "policy-matrix",
                    "seed_bundle": "seeds.json",
                    "include_ablations": True,
                    "runtime": {
                        "scenario_path": "scenarios/baselines/rule_baseline.json",
                        "horizon": 2,
                        "runs_root": "artifacts/runs",
                        "metrics_root": "artifacts/metrics",
                        "reports_root": "artifacts/reports",
                    },
                }
            ),
            encoding="utf-8",
        )

        captured: dict = {}

        def _fake_run_policy_experiment_matrix(**kwargs):
            captured.update(kwargs)
            return {
                "report_file": "artifacts/reports/matrix.json",
                "report": {
                    "matrix_metadata": {
                        "scenario_id": "containment-stress",
                        "seed_count": len(kwargs["seeds"]),
                        "horizon": kwargs["horizon"],
                        "condition_count": 4,
                        "include_ablations": kwargs["include_ablations"],
                    }
                },
            }

        monkeypatch.setattr(experiment_commands, "run_policy_experiment_matrix", _fake_run_policy_experiment_matrix)

        experiment_commands.run_policy_experiment_matrix_main(
            [
                "--config",
                str(preset),
                "--scenario",
                "scenarios/library/containment_stress.json",
                "--horizon",
                "5",
                "--skip-ablations",
            ]
        )

        assert captured["scenario_path"] == Path("scenarios/library/containment_stress.json")
        assert captured["seeds"] == [777, 888]
        assert captured["horizon"] == 5
        assert captured["include_ablations"] is False
