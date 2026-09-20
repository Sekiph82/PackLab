"""User-local PackLab cache, temporary workspace, and durable-data paths."""

from __future__ import annotations

import os
import platform
from collections.abc import Mapping
from pathlib import Path


def _default_root(system: str, env: Mapping[str, str], home: Path) -> Path:
    if system == "Windows":
        return Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local") / "PackLab"
    if system == "Darwin":
        return home / "Library" / "Caches" / "PackLab"
    return Path(env.get("XDG_CACHE_HOME") or home / ".cache") / "packlab"


def cache_root(
    *, env: Mapping[str, str] | None = None, home: Path | None = None, system: str | None = None
) -> Path:
    """Return the cache root without creating it or reading protected data."""

    values = os.environ if env is None else env
    selected_home = Path.home() if home is None else Path(home)
    selected_system = platform.system() if system is None else system
    override = values.get("PACKLAB_CACHE_ROOT")
    return (
        Path(override).expanduser()
        if override
        else _default_root(selected_system, values, selected_home)
    )


def workspace_root(
    *, env: Mapping[str, str] | None = None, home: Path | None = None, system: str | None = None
) -> Path:
    """Return a disposable per-job workspace below the cache root."""

    return cache_root(env=env, home=home, system=system) / "work"


def project_data_root(
    *, env: Mapping[str, str] | None = None, home: Path | None = None, system: str | None = None
) -> Path:
    """Return durable user/project data, kept distinct from regenerable cache data."""

    values = os.environ if env is None else env
    override = values.get("PACKLAB_DATA_ROOT")
    if override:
        return Path(override).expanduser()
    selected_home = Path.home() if home is None else Path(home)
    selected_system = platform.system() if system is None else system
    if selected_system == "Windows":
        return (
            Path(values.get("LOCALAPPDATA") or selected_home / "AppData" / "Local")
            / "PackLab"
            / "data"
        )
    if selected_system == "Darwin":
        return selected_home / "Library" / "Application Support" / "PackLab"
    return Path(values.get("XDG_DATA_HOME") or selected_home / ".local" / "share") / "packlab"


def ensure_directories(
    *, env: Mapping[str, str] | None = None, home: Path | None = None, system: str | None = None
) -> dict[str, Path]:
    """Create only PackLab-owned directories and never remove existing data."""

    roots = {
        "cache": cache_root(env=env, home=home, system=system),
        "workspace": workspace_root(env=env, home=home, system=system),
        "project_data": project_data_root(env=env, home=home, system=system),
    }
    for path in roots.values():
        path.mkdir(parents=True, exist_ok=True)
    return roots
