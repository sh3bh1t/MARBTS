from __future__ import annotations

from pathlib import Path

from marbts_cli.container_commands import run_container_profile_main
from utils.container_specs import (
    build_default_container_execution_specs,
    build_docker_compose_run_command,
    get_container_execution_spec,
)


def test_container_specs_cover_canonical_phase6_workflows() -> None:
    specs = {spec.spec_id: spec for spec in build_default_container_execution_specs()}

    assert set(specs) == {
        "multi_seed_baseline",
        "policy_matrix_baseline",
        "stress_suite_baseline",
        "ablation_report_baseline",
    }
    assert specs["multi_seed_baseline"].marbts_command == (
        "multi-seed-report",
        "--config",
        "configs/experiments/multi_seed_baseline.json",
    )
    assert specs["policy_matrix_baseline"].marbts_command == (
        "policy-experiment-matrix",
        "--config",
        "configs/experiments/policy_experiment_matrix_baseline.json",
    )
    assert specs["stress_suite_baseline"].marbts_command == (
        "stress-test-suite",
        "--config",
        "configs/experiments/stress_test_suite_baseline.json",
    )
    assert specs["ablation_report_baseline"].marbts_command == (
        "ablation-report",
        "--config",
        "configs/experiments/ablation_report_baseline.json",
        "--containerized",
    )


def test_build_docker_compose_run_command_supports_flags_and_passthrough_args() -> None:
    spec = get_container_execution_spec("policy_matrix_baseline")

    command = build_docker_compose_run_command(
        spec,
        compose_file="docker/docker-compose.yml",
        docker_binary="docker",
        remove_container=False,
        build_image=True,
        service_args=["--horizon", "1", "--skip-ablations"],
    )

    assert command == (
        "docker",
        "compose",
        "-f",
        "docker/docker-compose.yml",
        "--profile",
        "policy-matrix",
        "run",
        "--build",
        "policy-experiment-matrix",
        "--horizon",
        "1",
        "--skip-ablations",
    )


def test_container_profile_command_dry_run_does_not_execute_subprocess(monkeypatch, capsys) -> None:
    captured = {"called": False}

    def _fake_run(*_args, **_kwargs):
        captured["called"] = True
        raise AssertionError("subprocess.run should not be called in dry-run mode")

    monkeypatch.setattr("marbts_cli.container_commands.subprocess.run", _fake_run)

    run_container_profile_main(["--spec", "multi_seed_baseline", "--dry-run"])

    stdout = capsys.readouterr().out
    assert "CONTAINER_PROFILE_READY" in stdout
    assert "spec_id=multi_seed_baseline" in stdout
    assert "dry_run=true" in stdout
    assert captured["called"] is False


def test_container_profile_command_executes_subprocess(monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}

    class _Result:
        returncode = 0

    def _fake_run(command, *, check):
        captured["command"] = tuple(command)
        captured["check"] = check
        return _Result()

    monkeypatch.setattr("marbts_cli.container_commands.subprocess.run", _fake_run)

    run_container_profile_main(["--spec", "stress_suite_baseline"])

    stdout = capsys.readouterr().out
    assert "CONTAINER_PROFILE_OK" in stdout
    assert captured["check"] is False
    assert captured["command"] == (
        "docker",
        "compose",
        "-f",
        "docker/docker-compose.yml",
        "--profile",
        "stress-suite",
        "run",
        "--rm",
        "stress-test-suite",
    )


def test_docker_assets_match_container_specs() -> None:
    dockerfile_text = Path("docker/Dockerfile").read_text(encoding="utf-8")
    compose_text = Path("docker/docker-compose.yml").read_text(encoding="utf-8")

    assert 'FROM python:3.12-slim' in dockerfile_text
    assert 'ENTRYPOINT ["marbts"]' in dockerfile_text
    assert 'python -m pip install -e .' in dockerfile_text
    assert "services:" in compose_text

    for spec in build_default_container_execution_specs():
        assert f"{spec.service_name}:" in compose_text
        assert f'profiles: ["{spec.compose_profile}"]' in compose_text
        command_literal = ", ".join(f'"{token}"' for token in spec.marbts_command)
        assert f"command: [{command_literal}]" in compose_text
