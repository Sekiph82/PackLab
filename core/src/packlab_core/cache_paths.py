"""User-local PackLab cache, temporary workspace, and durable-data paths."""

from __future__ import annotations

import os
import platform
from collections.abc import Mapping
from pathlib import Path


def _validate_cache_data_roots(cache: Path, project_data: Path) -> None:
    """Reject overlapping ownership roots before any directory is created."""

    resolved_cache = cache.expanduser().resolve(strict=False)
    resolved_data = project_data.expanduser().resolve(strict=False)
    if (
        resolved_cache == resolved_data
        or resolved_data in resolved_cache.parents
        or resolved_cache in resolved_data.parents
    ):
        raise ValueError(
            "PACKLAB_CACHE_ROOT and PACKLAB_DATA_ROOT must be distinct, "
            f"non-overlapping roots; cache={resolved_cache}, data={resolved_data}"
        )


def _default_root(system: str, env: Mapping[str, str], home: Path) -> Path:
    if system == "Windows":
        return (
            Path(env.get("LOCALAPPDATA") or home / "AppData" / "Local")
            / "PackLab"
            / "cache"
        )
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
    selected_home = Path.home() if home is None else Path(home)
    selected_system = platform.system() if system is None else system
    if override:
        data_root = Path(override).expanduser()
    elif selected_system == "Windows":
        data_root = (
            Path(values.get("LOCALAPPDATA") or selected_home / "AppData" / "Local")
            / "PackLab"
            / "data"
        )
    elif selected_system == "Darwin":
        data_root = selected_home / "Library" / "Application Support" / "PackLab"
    else:
        data_root = Path(values.get("XDG_DATA_HOME") or selected_home / ".local" / "share") / "packlab"
    _validate_cache_data_roots(
        cache_root(env=values, home=selected_home, system=selected_system), data_root
    )
    return data_root


def ensure_directories(
    *, env: Mapping[str, str] | None = None, home: Path | None = None, system: str | None = None
) -> dict[str, Path]:
    """Create only PackLab-owned directories and never remove existing data."""

    roots = {
        "cache": cache_root(env=env, home=home, system=system),
        "workspace": workspace_root(env=env, home=home, system=system),
        "project_data": project_data_root(env=env, home=home, system=system),
    }
    _validate_cache_data_roots(roots["cache"], roots["project_data"])
    for path in roots.values():
        path.mkdir(parents=True, exist_ok=True)
    return roots
