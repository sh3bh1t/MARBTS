from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from utils.release_validation import run_release_validation


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run MARBTS release-readiness gate validation.",
    )
    parser.add_argument(
        "--reports-root",
        default=None,
        help="Optional directory root for writing the release readiness report JSON.",
    )
    return parser


def run_release_validation_main(argv: Sequence[str] | None = None) -> None:
    args = _build_parser().parse_args(argv)
    reports_root = Path(args.reports_root) if args.reports_root else None

    result = run_release_validation(reports_root=reports_root)
    report = result["report"]

    status_tag = "RELEASE_READY" if report.all_gates_pass else "RELEASE_NOT_READY"
    print(status_tag)
    print(f"timestamp_utc={report.timestamp_utc}")
    print(f"gate_count={report.gate_count}")
    print(f"pass_count={report.pass_count}")
    print(f"fail_count={report.fail_count}")
    print(f"all_gates_pass={str(report.all_gates_pass).lower()}")
    for gate in report.gates:
        symbol = "PASS" if gate.status == "pass" else "FAIL"
        detail = gate.evidence if gate.status == "pass" else gate.failure_detail
        print(f"  [{symbol}] {gate.gate_id}: {detail or gate.description}")
    if result["report_file"] is not None:
        print(f"report_file={result['report_file']}")

    if not report.all_gates_pass:
        raise SystemExit(1)
