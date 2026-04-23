from __future__ import annotations

import argparse
import subprocess
from datetime import datetime, timezone
from typing import Sequence

from utils.container_specs import (
    DEFAULT_COMPOSE_FILE,
    build_default_container_execution_specs,
    build_docker_compose_run_command,
    get_container_execution_spec,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run canonical MARBTS Docker Compose container profiles.",
    )
    parser.add_argument(
        "--spec",
        default="multi_seed_baseline",
        choices=sorted(spec.spec_id for spec in build_default_container_execution_specs()),
        help="Container execution spec identifier.",
    )
    parser.add_argument(
        "--compose-file",
        default=DEFAULT_COMPOSE_FILE,
        help="Path to docker compose file.",
    )
    parser.add_argument(
        "--docker-binary",
        default="docker",
        help="Docker CLI executable name/path.",
    )
    parser.add_argument(
        "--build",
        action="store_true",
        help="Build image before running the selected service.",
    )
    parser.add_argument(
        "--no-rm",
        action="store_true",
        help="Do not pass --rm to docker compose run.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the resolved docker compose command without executing it.",
    )
    parser.add_argument(
        "service_args",
        nargs=argparse.REMAINDER,
        help="Optional extra args passed to the compose service command.",
    )
    return parser


def _normalize_service_args(raw_args: Sequence[str]) -> list[str]:
    service_args = list(raw_args)
    if service_args and service_args[0] == "--":
        return service_args[1:]
    return service_args


def run_container_profile_main(argv: Sequence[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    spec = get_container_execution_spec(args.spec)
    service_args = _normalize_service_args(args.service_args)

    command = build_docker_compose_run_command(
        spec,
        compose_file=args.compose_file,
        docker_binary=args.docker_binary,
        remove_container=not args.no_rm,
        build_image=args.build,
        service_args=service_args,
    )

    print("CONTAINER_PROFILE_READY")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"spec_id={spec.spec_id}")
    print(f"service_name={spec.service_name}")
    print(f"compose_profile={spec.compose_profile}")
    print(f"command={' '.join(command)}")
    print(f"marbts_command={' '.join(spec.marbts_command)}")

    if args.dry_run:
        print("dry_run=true")
        return

    completed = subprocess.run(command, check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)

    print("CONTAINER_PROFILE_OK")

