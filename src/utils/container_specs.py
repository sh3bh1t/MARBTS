from __future__ import annotations

from typing import Sequence

from hart.models import ContainerExecutionSpec


DEFAULT_COMPOSE_FILE = "docker/docker-compose.yml"

_DEFAULT_CONTAINER_SPECS = (
    ContainerExecutionSpec(
        spec_id="multi_seed_baseline",
        service_name="multi-seed-report",
        compose_profile="multi-seed",
        description="Run canonical multi-seed baseline report in a container.",
        marbts_subcommand="multi-seed-report",
        preset_config_path="configs/experiments/multi_seed_baseline.json",
    ),
    ContainerExecutionSpec(
        spec_id="policy_matrix_baseline",
        service_name="policy-experiment-matrix",
        compose_profile="policy-matrix",
        description="Run canonical adaptive-vs-rule matrix baseline in a container.",
        marbts_subcommand="policy-experiment-matrix",
        preset_config_path="configs/experiments/policy_experiment_matrix_baseline.json",
    ),
    ContainerExecutionSpec(
        spec_id="stress_suite_baseline",
        service_name="stress-test-suite",
        compose_profile="stress-suite",
        description="Run canonical stress-suite baseline in a container.",
        marbts_subcommand="stress-test-suite",
        preset_config_path="configs/experiments/stress_test_suite_baseline.json",
    ),
    ContainerExecutionSpec(
        spec_id="ablation_report_baseline",
        service_name="ablation-report",
        compose_profile="ablation-report",
        description="Run canonical ablation report package baseline in a container.",
        marbts_subcommand="ablation-report",
        preset_config_path="configs/experiments/ablation_report_baseline.json",
        additional_args=("--containerized",),
    ),
)


def build_default_container_execution_specs() -> tuple[ContainerExecutionSpec, ...]:
    return _DEFAULT_CONTAINER_SPECS


def get_container_execution_spec(spec_id: str) -> ContainerExecutionSpec:
    normalized = spec_id.strip()
    if not normalized:
        raise ValueError("spec_id must be a non-empty string")

    for spec in _DEFAULT_CONTAINER_SPECS:
        if spec.spec_id == normalized:
            return spec

    raise KeyError(f"unknown container execution spec: {spec_id}")


def build_docker_compose_run_command(
    spec: ContainerExecutionSpec,
    *,
    compose_file: str = DEFAULT_COMPOSE_FILE,
    docker_binary: str = "docker",
    remove_container: bool = True,
    build_image: bool = False,
    service_args: Sequence[str] = (),
) -> tuple[str, ...]:
    if not compose_file.strip():
        raise ValueError("compose_file must be a non-empty string")
    if not docker_binary.strip():
        raise ValueError("docker_binary must be a non-empty string")

    command = [
        docker_binary,
        "compose",
        "-f",
        compose_file,
        "--profile",
        spec.compose_profile,
        "run",
    ]

    if remove_container:
        command.append("--rm")
    if build_image:
        command.append("--build")

    command.append(spec.service_name)
    command.extend(str(arg) for arg in service_args)
    return tuple(command)
