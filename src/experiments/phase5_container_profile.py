from __future__ import annotations

import json
from pathlib import Path
import shlex

from hart.models import ContainerExecutionConfig


def load_container_execution_config(path: str | Path) -> ContainerExecutionConfig:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("container execution config root must be an object")

    return ContainerExecutionConfig(
        image_name=str(payload["image_name"]),
        workdir=str(payload["workdir"]),
        entrypoint=str(payload["entrypoint"]),
        requirements_file=str(payload["requirements_file"]),
    )


def build_container_run_command(
    config: ContainerExecutionConfig,
    *,
    script_path: str,
    extra_args: tuple[str, ...] = (),
) -> str:
    quoted_args = " ".join(shlex.quote(arg) for arg in extra_args)
    python_command = f"PYTHONPATH=src python {shlex.quote(script_path)}"
    if quoted_args:
        python_command = f"{python_command} {quoted_args}"
    entrypoint = " ".join(shlex.quote(token) for token in shlex.split(config.entrypoint))

    return (
        "docker run --rm "
        f"-v $PWD:{shlex.quote(config.workdir)} "
        f"-w {shlex.quote(config.workdir)} "
        f"{shlex.quote(config.image_name)} "
        f"{entrypoint} {shlex.quote(f'python -m pip install -r {config.requirements_file} && {python_command}')}"
    )
