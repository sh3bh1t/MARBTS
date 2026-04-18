from pathlib import Path
import tempfile

from experiments.phase3_unified_comparison import run_phase3_unified_comparison
from hart.models import AdaptivePolicyConfig
from visualization.reporting import write_phase3_markdown_summary


class _FakeParsedResponse:
    def __init__(self, output_parsed) -> None:
        self.output_parsed = output_parsed


class _FakeClient:
    def __init__(self) -> None:
        self.responses = self

    def parse(self, **kwargs):
        actor_prompt = kwargs["input"][0]["content"]
        if "Actor: blue" in actor_prompt:
            payload = type(
                "DecisionPayload",
                (),
                {
                    "action_type": "monitor",
                    "targets": ["db-1"],
                    "summary": "Monitor the database.",
                    "predicted_effect": "Increase visibility on the database.",
                    "confidence": 0.7,
                    "utility_estimate": 5.0,
                },
            )()
        else:
            payload = type(
                "DecisionPayload",
                (),
                {
                    "action_type": "scan",
                    "targets": ["srv-1"],
                    "summary": "Scan the server.",
                    "predicted_effect": "Gather reconnaissance.",
                    "confidence": 0.7,
                    "utility_estimate": 5.0,
                },
            )()
        return _FakeParsedResponse(payload)


def test_phase3_unified_report_contains_ablation_conditions() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = run_phase3_unified_comparison(
            scenario_path="scenarios/baselines/phase2_rule_baseline.json",
            seeds=[20260329],
            horizon=4,
            planner_config=AdaptivePolicyConfig(backend="planning", planning_depth=3),
            llm_config=AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini"),
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
            client_factory=_FakeClient,
        )

        report = output["report"]
        assert Path(output["report_file"]).exists()
        assert any(item["condition_id"] == "rule_vs_planner_blue_no_planning" for item in report["aggregates"])
        assert any(item["condition_id"] == "rule_vs_rl_blue" for item in report["aggregates"])
        assert any(item["condition_id"] == "rule_vs_rl_blue_reduced_observability" for item in report["aggregates"])
        assert any(item["condition_id"] == "rule_vs_llm_blue_reduced_observability" for item in report["aggregates"])
        assert report["rl_config"]["backend"] == "rl"

        summary_path = write_phase3_markdown_summary(report, Path(temp_dir) / "reports" / "phase3-unified.md")
        summary_text = Path(summary_path).read_text(encoding="utf-8")
        assert "rule_vs_planner_blue_no_planning" in summary_text
        assert "rule_vs_rl_blue" in summary_text
        assert "rule_vs_llm_blue_reduced_observability" in summary_text
