from __future__ import annotations

import argparse
import json
from pathlib import Path

from simulation.artifact_loader import load_comparison_report, load_run_artifacts, reconstruct_run_replay, validate_run_artifacts
from visualization.replay_reports import write_phase4_comparison_html, write_phase4_dashboard_html, write_run_replay_markdown


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Phase 4 replay/comparison outputs from existing artifacts.")
    parser.add_argument("--run-dir", required=True, help="Path to an existing run artifact directory.")
    parser.add_argument("--report-file", required=True, help="Path to an existing comparison JSON report.")
    parser.add_argument(
        "--output-dir",
        default="artifacts/reports",
        help="Directory for generated Phase 4 report outputs.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_artifacts = load_run_artifacts(args.run_dir)
    validation_payload = validate_run_artifacts(run_artifacts)
    replay_frames = reconstruct_run_replay(run_artifacts)
    comparison_report = load_comparison_report(args.report_file)

    output_dir = Path(args.output_dir)
    replay_path = write_run_replay_markdown(
        run_artifacts,
        replay_frames,
        output_dir / f"phase4_replay_{run_artifacts['metadata']['run_id']}.md",
    )
    dashboard_path = write_phase4_dashboard_html(
        comparison_report,
        validation_payload,
        Path(replay_path).name,
        output_dir / "phase4_dashboard_from_artifacts.html",
    )
    comparison_path = write_phase4_comparison_html(
        comparison_report,
        output_dir / "phase4_comparison_from_artifacts.html",
    )

    print(
        json.dumps(
            {
                "replay_markdown_file": replay_path,
                "dashboard_html_file": dashboard_path,
                "comparison_html_file": comparison_path,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
