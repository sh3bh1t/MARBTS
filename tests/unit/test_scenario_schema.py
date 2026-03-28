import unittest

from marbts.schemas.scenario import load_scenario_file, validate_scenario_dict


def _valid_scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "baseline-small", "version": "1.0.0"},
        "nodes": [
            {
                "node_id": "srv-1",
                "node_type": "server",
                "services": ["ssh", "http"],
                "vulnerabilities": ["cve-sim-001"],
                "security_level": 3,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": False,
            },
            {
                "node_id": "db-1",
                "node_type": "database",
                "services": ["postgres"],
                "vulnerabilities": ["cve-sim-010"],
                "security_level": 4,
                "compromised_state": "none",
                "detection_state": "undetected",
                "isolation_state": False,
            },
        ],
        "edges": [{"source": "srv-1", "target": "db-1"}],
    }


class TestScenarioSchema(unittest.TestCase):
    def test_validate_valid_scenario(self) -> None:
        scenario = validate_scenario_dict(_valid_scenario_dict())
        self.assertEqual(scenario.metadata.scenario_id, "baseline-small")
        self.assertEqual(len(scenario.nodes), 2)
        self.assertEqual(len(scenario.edges), 1)

    def test_reject_missing_required_node_field(self) -> None:
        payload = _valid_scenario_dict()
        del payload["nodes"][0]["security_level"]

        with self.assertRaisesRegex(ValueError, "missing required fields"):
            validate_scenario_dict(payload)

    def test_reject_edge_with_unknown_node_reference(self) -> None:
        payload = _valid_scenario_dict()
        payload["edges"] = [{"source": "srv-1", "target": "ghost-node"}]

        with self.assertRaisesRegex(ValueError, "references undefined node_id"):
            validate_scenario_dict(payload)

    def test_load_valid_baseline_file(self) -> None:
        scenario = load_scenario_file("scenarios/baselines/minimal_valid.json")
        self.assertEqual(scenario.metadata.version, "1.0.0")


if __name__ == "__main__":
    unittest.main()
