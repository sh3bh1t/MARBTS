from experiments.phase5_container_profile import build_container_run_command, load_container_execution_config


def test_container_profile_load_and_command_render() -> None:
    config = load_container_execution_config("configs/base/phase5_container_profile.json")

    assert config.image_name == "marbts-phase5:latest"
    command = build_container_run_command(config, script_path="scripts/run_phase5_ablation_smoke.py")

    assert "docker run --rm" in command
    assert "marbts-phase5:latest" in command
    assert "scripts/run_phase5_ablation_smoke.py" in command
