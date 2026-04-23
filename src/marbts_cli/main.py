from __future__ import annotations

import argparse
from typing import Sequence

from .container_commands import run_container_profile_main
from .experiment_commands import (
    run_ablation_report_main,
    run_multi_seed_report_main,
    run_policy_experiment_matrix_main,
    run_stress_test_suite_main,
)


COMMANDS = {
    "multi-seed-report": run_multi_seed_report_main,
    "policy-experiment-matrix": run_policy_experiment_matrix_main,
    "stress-test-suite": run_stress_test_suite_main,
    "ablation-report": run_ablation_report_main,
    "container-profile": run_container_profile_main,
}


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="marbts",
        description="MARBTS packaged CLI. Use subcommands for experiment workflows.",
    )
    subparsers = parser.add_subparsers(dest="command")
    for name in COMMANDS:
        subparsers.add_parser(name, add_help=False)

    known_args, remaining_args = parser.parse_known_args(argv)
    if known_args.command is None:
        parser.print_help()
        return

    COMMANDS[known_args.command](remaining_args)
