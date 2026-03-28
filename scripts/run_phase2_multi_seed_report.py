from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from experiments.phase2_comparison import run_phase2_multi_seed_report


def main() -> None:
    scenario_path = Path("scenarios/baselines/phase2_rule_baseline.json")
    seeds = [20260329, 20260330, 20260331]
    horizon = 8

    output = run_phase2_multi_seed_report(
        scenario_path=scenario_path,
        seeds=seeds,
        horizon=horizon,
    )

    aggregate = output["report"]["aggregate"]
    print("PHASE2_MULTI_SEED_REPORT_OK")
    print(f"timestamp_utc={datetime.now(timezone.utc).isoformat()}")
    print(f"scenario_id={aggregate['scenario_id']}")
    print(f"seed_count={aggregate['seed_count']}")
    print(f"final_compromised_mean={aggregate['final_compromised_mean']}")
    print(f"report_file={output['report_file']}")


if __name__ == "__main__":
    main()