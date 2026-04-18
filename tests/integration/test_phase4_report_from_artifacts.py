from pathlib import Path
import tempfile

from experiments.phase3_unified_comparison import run_phase3_unified_comparison
from hart.models import AdaptivePolicyConfig
from simulation.artifact_loader import load_run_artifacts
from visualization.replay_reports import write_phase4_comparison_html


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


def test_phase4_comparison_html_from_existing_report() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        comparison = run_phase3_unified_comparison(
            scenario_path="scenarios/baselines/phase2_rule_baseline.json",
            seeds=[20260329],
            horizon=4,
            planner_config=AdaptivePolicyConfig(backend="planning", planning_depth=3),
            llm_config=AdaptivePolicyConfig(backend="openai", model_name="gpt-5-mini"),
            runs_root=Path(temp_dir) / "runs",
            reports_root=Path(temp_dir) / "reports",
            client_factory=_FakeClient,
        )
        html_path = write_phase4_comparison_html(
            comparison["report"],
            Path(temp_dir) / "reports" / "comparison.html",
        )
        assert Path(html_path).exists()
        assert "Phase 4 Comparison Report" in Path(html_path).read_text(encoding="utf-8")

        first_run_dir = comparison["report"]["runs"][0]["run_dir"]
        loaded = load_run_artifacts(first_run_dir)
        assert loaded["metadata"]["run_id"]
