from pathlib import Path
import tempfile

from experiments.phase3_llm_comparison import run_phase3_llm_comparison
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


def test_phase3_llm_report_and_markdown_summary() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = run_phase3_llm_comparison(
            scenario_path="scenarios/baselines/phase2_rule_baseline.json",
            seeds=[20260329],
            horizon=4,
            llm_config=AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini"),
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
            client_factory=_FakeClient,
        )

        report = output["report"]
        assert Path(output["report_file"]).exists()
        assert any(item["condition_id"] == "rule_vs_llm_blue" for item in report["aggregates"])
        assert report["llm_config"]["backend"] == "openai"

        summary_path = write_phase3_markdown_summary(report, Path(temp_dir) / "reports" / "phase3-llm.md")
        summary_text = Path(summary_path).read_text(encoding="utf-8")
        assert "rule_vs_llm_blue" in summary_text
