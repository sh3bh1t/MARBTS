from __future__ import annotations

from pathlib import Path

from marbts_ui.server import (
    api_container_profile,
    api_run_simulation,
    api_scenario_detail,
    api_validate_scenario,
)


def test_ui_scenario_detail_and_validation() -> None:
    detail = api_scenario_detail("scenarios/baselines/rule_baseline.json")

    assert detail["summary"]["scenario_id"] == "rule-baseline"
    assert detail["graph"]["stats"]["node_count"] == 4
    assert detail["graph"]["stats"]["edge_count"] == 3

    validation = api_validate_scenario({"payload": detail["raw"]})

    assert validation["ok"] is True
    assert validation["summary"]["vulnerabilities_count"] == 4


def test_ui_run_simulation_writes_artifacts(tmp_path: Path) -> None:
    output = api_run_simulation(
        {
            "scenario_path": "scenarios/baselines/rule_baseline.json",
            "seed": 20260329,
            "horizon": 2,
            "red_policy": "rule",
            "blue_policy": "rule",
            "runs_root": str(tmp_path / "runs"),
            "metrics_root": str(tmp_path / "metrics"),
            "reports_root": str(tmp_path / "reports"),
        }
    )

    assert output["metadata"]["scenario_id"] == "rule-baseline"
    assert output["baseline_metrics"]["timesteps_count"] == 2
    assert len(output["timeline"]) == 2
    assert Path(output["artifacts"]["run_dir"]).exists()
    assert Path(output["baseline_metrics_file"]).exists()


def test_ui_container_profile_dry_run() -> None:
    output = api_container_profile(
        {
            "spec_id": "multi_seed_baseline",
            "build_image": True,
            "execute": False,
        }
    )

    assert output["dry_run"] is True
    assert output["spec"]["spec_id"] == "multi_seed_baseline"
    assert "docker compose" in output["command_text"]
    assert "--build" in output["command"]
