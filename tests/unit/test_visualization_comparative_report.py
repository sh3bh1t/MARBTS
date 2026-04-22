from __future__ import annotations

from pathlib import Path
import tempfile

from environment.graph_builder import build_graph_from_scenario
from schemas.scenario import validate_scenario_dict
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts

from visualization.comparative_report import generate_comparative_report


def _scenario_dict() -> dict:
    return {
        "metadata": {"scenario_id": "comparison-small", "version": "1.0.0"},
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


def test_generate_comparative_report_writes_pairwise_summary() -> None:
    scenario = validate_scenario_dict(_scenario_dict())

    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        graph_one = build_graph_from_scenario(scenario)
        graph_two = build_graph_from_scenario(scenario)

        result_one = run_turn_based_simulation(graph_one, seed=42, horizon=3, scenario_id="comparison-small")
        result_two = run_turn_based_simulation(graph_two, seed=43, horizon=3, scenario_id="comparison-small")

        run_one_paths = write_run_artifacts(result_one, root / "runs")
        run_two_paths = write_run_artifacts(result_two, root / "runs")

        output = generate_comparative_report(
            left_run_dir=run_one_paths["run_dir"],
            right_run_dir=run_two_paths["run_dir"],
            reports_root=root / "reports",
            figures_root=root / "figures",
        )

        report_file = Path(output["report_file"])
        summary_file = Path(output["summary_file"])
        report = output["report"]

        assert report_file.exists()
        assert summary_file.exists()
        assert report["report_summary"]["scenario_id"] == "comparison-small__vs__comparison-small"
        assert report["left_run"]["sequence_hash_matches"] is True
        assert report["right_run"]["sequence_hash_matches"] is True
        assert "final_compromised_nodes_delta" in report["comparisons"]
        assert "sequence_hash_match" in report["comparisons"]
        assert report["comparisons"]["sequence_hash_integrity"] is True
        assert "response_latency_delta" in report["comparisons"]
        assert "analysis" in report
        assert report["analysis"]["left_run"]["response_latency"] >= -1
        assert report["analysis"]["right_run"]["response_latency"] >= -1

        for figure_path in output["figure_files"].values():
            assert Path(figure_path).exists()

        assert "defense_efficiency" in report["visualizations"]
        assert "response_latency" in report["visualizations"]