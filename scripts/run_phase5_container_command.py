from __future__ import annotations

import json

from experiments.phase5_container_profile import build_container_run_command, load_container_execution_config


def main() -> None:
    config = load_container_execution_config("configs/base/phase5_container_profile.json")
    command = build_container_run_command(
        config,
        script_path="scripts/run_phase5_ablation_smoke.py",
    )
    print(json.dumps({"container_command": command}, indent=2))


if __name__ == "__main__":
    main()
