from __future__ import annotations

import pytest

from observability.validation import validate_event_payload


def test_validate_event_payload_rejects_missing_schema_fields() -> None:
    with pytest.raises(ValueError, match="event envelope missing required fields"):
        validate_event_payload({"event_type": "timestep"})


def test_validate_event_payload_rejects_unsupported_event_type() -> None:
    with pytest.raises(ValueError, match="unsupported event_type"):
        validate_event_payload(
            {
                "schema_version": "2026-04-23.observability.v1",
                "event_type": "unknown",
                "provenance": {
                    "schema_version": "2026-04-23.observability.v1",
                    "run_id": "run-1",
                    "scenario_id": "scenario-1",
                    "seed": 1,
                    "horizon": 1,
                    "config_hash": "abc",
                    "commit_hash": "def",
                    "timestamp_utc": "2026-04-23T00:00:00Z",
                },
            }
        )