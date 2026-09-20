"""Typed PackLab configuration with deterministic, safe precedence."""

from __future__ import annotations

import os
import platform
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when a configuration file or environment value is unsafe/invalid."""


@dataclass(frozen=True)
class AppConfig:
    log_level: str = "INFO"
    telemetry_enabled: bool = False
    diagnostics_retention_days: int = 7
    cache_root: str | None = None


_FIELDS = {"log_level", "telemetry_enabled", "diagnostics_retention_days", "cache_root"}
_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR"}


def user_config_path(
    *, env: Mapping[str, str] | None = None, home: Path | None = None, system: str | None = None
) -> Path:
    values = os.environ if env is None else env
    selected_home = Path.home() if home is None else Path(home)
    selected_system = platform.system() if system is None else system
    if selected_system == "Windows":
        base = Path(values.get("APPDATA") or selected_home / "AppData" / "Roaming")
        return base / "PackLab" / "config.toml"
    if selected_system == "Darwin":
        return selected_home / "Library" / "Application Support" / "PackLab" / "config.toml"
    base = Path(values.get("XDG_CONFIG_HOME") or selected_home / ".config")
    return base / "packlab" / "config.toml"


def _validate(values: dict[str, Any], source: str) -> AppConfig:
    unknown = sorted(set(values) - _FIELDS)
    if unknown:
        raise ConfigError(f"{source}: unknown configuration key(s): {', '.join(unknown)}")
    if "log_level" in values and (
        not isinstance(values["log_level"], str) or values["log_level"].upper() not in _LEVELS
    ):
        raise ConfigError(f"{source}: log_level must be one of {sorted(_LEVELS)}")
    if "telemetry_enabled" in values and type(values["telemetry_enabled"]) is not bool:
        raise ConfigError(f"{source}: telemetry_enabled must be a boolean")
    if "diagnostics_retention_days" in values and (
        type(values["diagnostics_retention_days"]) is not int
        or not 1 <= values["diagnostics_retention_days"] <= 365
    ):
        raise ConfigError(f"{source}: diagnostics_retention_days must be an integer from 1 to 365")
    if (
        "cache_root" in values
        and values["cache_root"] is not None
        and not isinstance(values["cache_root"], str)
    ):
        raise ConfigError(f"{source}: cache_root must be a path string or null")
    normalized = dict(values)
    if "log_level" in normalized:
        normalized["log_level"] = normalized["log_level"].upper()
    return AppConfig(**normalized)


def _read_file(path: Path | None, source: str) -> dict[str, Any]:
    if path is None or not path.is_file():
        return {}
    try:
        with path.open("rb") as handle:
            values = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ConfigError(f"{source}: could not parse {path.name}: {exc}") from exc
    if not isinstance(values, dict):
        raise ConfigError(f"{source}: expected a TOML table")
    return values


def _environment(values: Mapping[str, str]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    if "PACKLAB_LOG_LEVEL" in values:
        result["log_level"] = values["PACKLAB_LOG_LEVEL"]
    if "PACKLAB_TELEMETRY_ENABLED" in values:
        raw = values["PACKLAB_TELEMETRY_ENABLED"].lower()
        if raw not in {"true", "false"}:
            raise ConfigError("environment: PACKLAB_TELEMETRY_ENABLED must be true or false")
        result["telemetry_enabled"] = raw == "true"
    if "PACKLAB_DIAGNOSTICS_RETENTION_DAYS" in values:
        raw = values["PACKLAB_DIAGNOSTICS_RETENTION_DAYS"]
        try:
            result["diagnostics_retention_days"] = int(raw)
        except ValueError as exc:
            raise ConfigError(
                "environment: PACKLAB_DIAGNOSTICS_RETENTION_DAYS must be an integer"
            ) from exc
    if "PACKLAB_CACHE_ROOT" in values:
        result["cache_root"] = values["PACKLAB_CACHE_ROOT"]
    return result


def load_config(
    *,
    project_path: Path | None = None,
    user_path: Path | None = None,
    env: Mapping[str, str] | None = None,
    home: Path | None = None,
    system: str | None = None,
) -> AppConfig:
    """Load defaults, then user config, project config, and environment overrides."""

    values: dict[str, Any] = {}
    sources = [
        (
            _read_file(
                user_path or user_config_path(env=env, home=home, system=system), "user config"
            ),
            "user config",
        ),
        (_read_file(project_path, "project config"), "project config"),
        (_environment(os.environ if env is None else env), "environment"),
    ]
    for source_values, source_name in sources:
        validated = _validate(source_values, source_name)
        values.update({key: getattr(validated, key) for key in source_values})
    return replace(AppConfig(), **values)
