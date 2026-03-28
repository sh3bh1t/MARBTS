from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from environment.graph_builder import build_graph_from_scenario
from metrics.baseline_metrics import compute_baseline_metrics, write_baseline_metrics_artifact
from schemas.scenario import load_scenario_file
from simulation.kernel import run_turn_based_simulation
from simulation.log_writer import write_run_artifacts


def _mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def run_phase2_multi_seed_report(
    *,
    scenario_path: str | Path,
    seeds: list[int],
    horizon: int,
    runs_root: str | Path = "artifacts/runs",
    metrics_root: str | Path = "artifacts/metrics",
    reports_root: str | Path = "artifacts/reports",
) -> dict:
    if not seeds:
        raise ValueError("seeds cannot be empty")

    scenario = load_scenario_file(scenario_path)
    per_run: list[dict] = []

    for seed in seeds:
        graph = build_graph_from_scenario(scenario)
        result = run_turn_based_simulation(
            graph,
            seed=seed,
            horizon=horizon,
            scenario_id=scenario.metadata.scenario_id,
        )

        run_artifacts = write_run_artifacts(result, runs_root)
        baseline_metrics_file = write_baseline_metrics_artifact(result, metrics_root)
        baseline_metrics = compute_baseline_metrics(result)

        per_run.append(
            {
                "run_id": result.metadata.run_id,
                "seed": seed,
                "sequence_hash": baseline_metrics["sequence_hash"],
                "final_compromised_nodes": baseline_metrics["security_outcomes"]["final_compromised_nodes"],
                "first_containment_timestep": baseline_metrics["policy_performance"]["first_containment_timestep"],
                "blue_containment_actions": baseline_metrics["policy_performance"]["blue_containment_actions"],
                "run_dir": run_artifacts["run_dir"],
                "baseline_metrics_file": baseline_metrics_file,
            }
        )

    final_compromised_values = [float(run["final_compromised_nodes"]) for run in per_run]
    containment_timesteps = [
        float(run["first_containment_timestep"])
        for run in per_run
        if run["first_containment_timestep"] >= 0
    ]

    aggregate = {
        "scenario_id": scenario.metadata.scenario_id,
        "scenario_version": scenario.metadata.version,
        "horizon": horizon,
        "seed_count": len(seeds),
        "seeds": seeds,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "final_compromised_mean": round(_mean(final_compromised_values), 3),
        "final_compromised_min": int(min(final_compromised_values)) if final_compromised_values else 0,
        "final_compromised_max": int(max(final_compromised_values)) if final_compromised_values else 0,
        "first_containment_mean": round(_mean(containment_timesteps), 3) if containment_timesteps else -1,
        "sequence_hashes": sorted({run["sequence_hash"] for run in per_run}),
    }

    report_payload = {
        "aggregate": aggregate,
        "runs": per_run,
    }

    report_dir = Path(reports_root)
    report_dir.mkdir(parents=True, exist_ok=True)
    report_file = report_dir / f"phase2_multi_seed_report_{scenario.metadata.scenario_id}.json"
    report_file.write_text(json.dumps(report_payload, indent=2, sort_keys=True), encoding="utf-8")

    return {
        "report_file": str(report_file),
        "report": report_payload,
    }