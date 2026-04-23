from __future__ import annotations

import json
import tempfile
from pathlib import Path

from experiments.ablation_report import build_container_execution_config, run_ablation_report_package


def test_ablation_report_package_writes_template_manifest_and_container_profile() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        container_execution = build_container_execution_config(
            scenario_path="scenarios/baselines/rule_baseline.json",
            seeds=[20260423, 20260424],
            horizon=2,
            include_ablations=True,
        )

        output = run_ablation_report_package(
            scenario_path="scenarios/baselines/rule_baseline.json",
            seeds=[20260423, 20260424],
            horizon=2,
            runs_root=root / "runs",
            metrics_root=root / "metrics",
            reports_root=root / "reports",
            include_ablations=True,
            containerized=True,
            container_image=container_execution.image,
            container_working_directory=container_execution.working_directory,
        )

        template_file = Path(output["template_file"])
        markdown_file = Path(output["markdown_file"])
        manifest_file = Path(output["manifest_file"])
        container_profile_file = Path(output["container_profile_file"])

        assert template_file.exists()
        assert markdown_file.exists()
        assert manifest_file.exists()
        assert container_profile_file.exists()

        template = json.loads(template_file.read_text(encoding="utf-8"))
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        container_profile = json.loads(container_profile_file.read_text(encoding="utf-8"))
        markdown = markdown_file.read_text(encoding="utf-8")

        assert template["template_metadata"]["scenario_id"] == "rule-baseline"
        assert template["template_metadata"]["condition_count"] == 14
        assert template["template_metadata"]["table_count"] == 2
        assert template["template_metadata"]["containerized"] is True
        assert len(template["publication_tables"]) == 2
        assert template["publication_tables"][0]["title"] == "Primary Ranking"
        assert template["publication_tables"][1]["title"] == "Condition Configuration"
        assert template["summary_rankings"]["lowest_final_compromised"]
        assert "Ablation Report Template" in markdown
        assert "Primary Ranking" in markdown
        assert Path(manifest["manifest_metadata"]["scenario_path"]).as_posix().endswith(
            "scenarios/baselines/rule_baseline.json"
        )
        assert template_file.as_posix() in [Path(path).as_posix() for path in manifest["artifact_files"]]
        assert markdown_file.as_posix() in [Path(path).as_posix() for path in manifest["artifact_files"]]
        assert Path(manifest["container_profile_file"]).as_posix() == container_profile_file.as_posix()
        assert container_profile["enabled"] is True
        assert container_profile["config_pin"].startswith("sha256:")
        assert container_profile["environment"]["PYTHONPATH"] == "src"
        assert container_profile["command"][0] == "python"