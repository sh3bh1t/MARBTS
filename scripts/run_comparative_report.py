from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

from visualization import generate_comparative_report


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a comparative report from two run artifact bundles.")
    parser.add_argument("--left-run-dir", required=True, help="Path to the left run artifact directory.")
    parser.add_argument("--right-run-dir", required=True, help="Path to the right run artifact directory.")
    parser.add_argument(
        "--reports-root",
        default="artifacts/reports",
        help="Output root for comparative report artifacts.",
    )
    parser.add_argument(
        "--output",
        help="Optional explicit output file path for the comparative report.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    output = generate_comparative_report(
        left_run_dir=Path(args.left_run_dir),
        right_run_dir=Path(args.right_run_dir),
        reports_root=Path(args.reports_root),
        output_path=Path(args.output) if args.output is not None else None,
    )

    report = output["report"]
    print("COMPARATIVE_REPORT_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"report_file={output['report_file']}")
    print(f"left_run_id={report['left_run']['run_id']}")
    print(f"right_run_id={report['right_run']['run_id']}")
    print(f"final_compromised_nodes_delta={report['comparisons']['final_compromised_nodes_delta']}")


if __name__ == "__main__":
    main()