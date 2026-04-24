from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]

NOTEBOOK_FILES = (
    "notebooks/replay_and_comparative_walkthrough.ipynb",
    "notebooks/policy_matrix_walkthrough.ipynb",
    "notebooks/ablation_report_walkthrough.ipynb",
)

REQUIRED_WORKFLOW_FIELDS = ("phase", "workflow_id", "generator_commands", "required_reports")


def _resolve_notebook_paths(notebook_paths: Iterable[str | Path]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    for notebook_path in notebook_paths:
        path = Path(notebook_path)
        if not path.is_absolute():
            path = ROOT / path
        resolved.append(path)
    return tuple(resolved)


def _load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"notebook must be a JSON object: {path}")
    return payload


def _validate_notebook_payload(path: Path, payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("nbformat") != 4:
        raise ValueError(f"unsupported nbformat in {path}: expected 4")
    cells = payload.get("cells")
    if not isinstance(cells, list) or not cells:
        raise ValueError(f"notebook has no cells: {path}")

    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"notebook metadata must be an object: {path}")
    workflow = metadata.get("marbts_workflow")
    if not isinstance(workflow, dict):
        raise ValueError(f"notebook metadata missing marbts_workflow: {path}")

    missing_fields = [field for field in REQUIRED_WORKFLOW_FIELDS if field not in workflow]
    if missing_fields:
        raise ValueError(f"notebook workflow metadata missing fields {missing_fields}: {path}")
    if not workflow["generator_commands"]:
        raise ValueError(f"notebook workflow generator_commands cannot be empty: {path}")

    code_cells = [cell for cell in cells if cell.get("cell_type") == "code"]
    if not code_cells:
        raise ValueError(f"notebook has no code cells: {path}")

    source_blob = "\n".join(
        "".join(cell.get("source", []))
        for cell in code_cells
        if isinstance(cell.get("source"), list)
    )
    if "RUN_GENERATORS" not in source_blob:
        raise ValueError(f"notebook missing RUN_GENERATORS control flag: {path}")
    if "scripts/run_" not in source_blob:
        raise ValueError(f"notebook missing canonical script reference: {path}")

    return {
        "path": str(path),
        "workflow_id": workflow["workflow_id"],
        "code_cell_count": len(code_cells),
    }


def validate_notebook_assets(notebook_paths: Iterable[str | Path] = NOTEBOOK_FILES) -> dict[str, Any]:
    resolved_paths = _resolve_notebook_paths(notebook_paths)
    if not resolved_paths:
        raise ValueError("notebook_paths cannot be empty")

    validated = []
    for notebook_path in resolved_paths:
        if not notebook_path.exists():
            raise FileNotFoundError(f"notebook file does not exist: {notebook_path}")
        payload = _load_json(notebook_path)
        validated.append(_validate_notebook_payload(notebook_path, payload))

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "notebook_count": len(validated),
        "workflows": validated,
    }


def main() -> None:
    summary = validate_notebook_assets()
    print("NOTEBOOK_SMOKE_OK")
    print(f"timestamp_utc={summary['timestamp_utc']}")
    print(f"notebook_count={summary['notebook_count']}")
    print(f"workflows={','.join(workflow['workflow_id'] for workflow in summary['workflows'])}")


if __name__ == "__main__":
    main()
