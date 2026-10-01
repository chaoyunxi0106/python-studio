from __future__ import annotations

from python_studio import domain_profiles


def test_builtin_domain_profiles_load() -> None:
    python_profile = domain_profiles.load_domain_profile("python")
    optimization = domain_profiles.load_domain_profile("optimization_math")

    assert python_profile.starter_file == "starter.py"
    assert python_profile.analysis_mode == "python_ast"
    assert optimization.starter_file == "starter.txt"
    assert optimization.analysis_mode == "generic"
    assert "{test_file}" in optimization.primary_command


def test_studio_config_can_be_updated(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "studio.json"
    monkeypatch.setattr(domain_profiles, "STUDIO_CONFIG", config_path)
    result = domain_profiles.update_studio_config(
        name="Optimization Studio",
        tagline="本地优化理论训练场",
        default_domain="optimization_math",
    )
    assert result["default_domain"] == "optimization_math"
    assert domain_profiles.load_studio_config()["name"] == "Optimization Studio"


def test_exercise_can_override_test_command() -> None:
    profile = domain_profiles.profile_for_exercise(
        {
            "domain": "command",
            "test_command": ["{python}", "custom_check.py"],
        }
    )
    command = domain_profiles.resolve_command(profile)
    assert command[1] == "custom_check.py"

