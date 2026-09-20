from pathlib import Path

import pytest

from packlab_core.config import ConfigError, load_config, user_config_path


def write_config(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def test_precedence_is_defaults_user_project_environment(tmp_path):
    user = tmp_path / "user.toml"
    project = tmp_path / "project.toml"
    write_config(user, 'log_level = "WARNING"\ntelemetry_enabled = true\n')
    write_config(project, 'log_level = "ERROR"\ndiagnostics_retention_days = 30\n')
    config = load_config(
        user_path=user,
        project_path=project,
        env={"PACKLAB_LOG_LEVEL": "debug", "PACKLAB_CACHE_ROOT": str(tmp_path / "cache")},
        home=tmp_path,
        system="Linux",
    )
    assert config.log_level == "DEBUG"
    assert config.telemetry_enabled is True
    assert config.diagnostics_retention_days == 30
    assert config.cache_root == str(tmp_path / "cache")


def test_missing_files_use_safe_defaults(tmp_path):
    config = load_config(
        user_path=tmp_path / "missing-user.toml",
        project_path=tmp_path / "missing-project.toml",
        home=tmp_path,
        system="Linux",
    )
    assert config.log_level == "INFO"
    assert config.telemetry_enabled is False


def test_malformed_and_unknown_values_are_actionable(tmp_path):
    malformed = tmp_path / "bad.toml"
    write_config(malformed, 'log_level = "TRACE"\n')
    with pytest.raises(ConfigError, match="log_level"):
        load_config(project_path=malformed, home=tmp_path, system="Linux")
    unknown = tmp_path / "unknown.toml"
    write_config(unknown, 'future_secret = "do-not-persist"\n')
    with pytest.raises(ConfigError, match="unknown"):
        load_config(project_path=unknown, home=tmp_path, system="Linux")


def test_environment_override_and_platform_paths(tmp_path):
    config = load_config(
        env={"PACKLAB_TELEMETRY_ENABLED": "true", "PACKLAB_DIAGNOSTICS_RETENTION_DAYS": "14"},
        home=tmp_path / "home",
        system="Windows",
    )
    assert config.telemetry_enabled is True
    assert config.diagnostics_retention_days == 14
    assert (
        user_config_path(
            env={"APPDATA": str(tmp_path / "appdata")}, home=tmp_path, system="Windows"
        )
        == tmp_path / "appdata" / "PackLab" / "config.toml"
    )
