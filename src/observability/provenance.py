from __future__ import annotations

from hashlib import sha256
import json
import subprocess

from hart.models import OBSERVABILITY_SCHEMA_VERSION, RunMetadata, RunProvenance


def _build_config_hash(metadata: RunMetadata) -> str:
    payload = {
        "horizon": metadata.horizon,
        "scenario_id": metadata.scenario_id,
        "seed": metadata.seed,
    }
    digest = sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:16]


def _build_commit_hash() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"

    commit_hash = completed.stdout.strip()
    return commit_hash or "unknown"


def collect_run_provenance(metadata: RunMetadata) -> RunProvenance:
    return RunProvenance(
        schema_version=OBSERVABILITY_SCHEMA_VERSION,
        run_id=metadata.run_id,
        scenario_id=metadata.scenario_id,
        seed=metadata.seed,
        horizon=metadata.horizon,
        config_hash=_build_config_hash(metadata),
        commit_hash=_build_commit_hash(),
        timestamp_utc=metadata.timestamp_utc,
    )