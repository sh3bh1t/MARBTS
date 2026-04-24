from __future__ import annotations

from pathlib import Path

from scripts.run_notebook_smoke import NOTEBOOK_FILES, validate_notebook_assets


def test_notebook_assets_validate_and_expose_expected_workflow_ids() -> None:
    summary = validate_notebook_assets()

    assert summary["notebook_count"] == 3
    workflow_ids = {workflow["workflow_id"] for workflow in summary["workflows"]}
    assert workflow_ids == {
        "replay_and_comparative",
        "policy_matrix",
        "ablation_report",
    }

    expected_paths = {str((Path.cwd() / notebook).resolve()) for notebook in NOTEBOOK_FILES}
    actual_paths = {str(Path(workflow["path"]).resolve()) for workflow in summary["workflows"]}
    assert actual_paths == expected_paths


def test_notebooks_stub_is_removed() -> None:
    assert not Path("notebooks/STUB.md").exists()
