"""Shared deployment classification for Windows native runtime dependencies."""

from __future__ import annotations

import re
from pathlib import Path

BUILD_ENV_CONDA_ONLY = {"ucrt", "vc14_runtime"}
_NUMPY_MSVCP_ALIAS = re.compile(r"^msvcp140-[0-9a-f]{32}\.dll$", re.IGNORECASE)


def is_windows_runtime_dll(path: Path | str) -> bool:
    name = Path(path).name.casefold()
    return (
        name.startswith(("api-ms-win-", "ext-ms-win-"))
        or name.startswith("ucrtbase")
        and name.endswith(".dll")
        or name.startswith(("msvcp140", "vcruntime140"))
        and name.endswith(".dll")
        or name in {"concrt140.dll", "vcomp140.dll"}
    )


def is_numpy_wheel_msvc_alias(destination: Path | str) -> bool:
    """Identify NumPy's exact wheel-private, hash-renamed MSVC runtime location."""
    normalized = str(destination).replace("\\", "/").casefold()
    parts = normalized.split("/")
    return (
        len(parts) >= 2
        and parts[-2] == "numpy.libs"
        and _NUMPY_MSVCP_ALIAS.fullmatch(parts[-1]) is not None
    )


def deployment_role(package_name: str) -> str | None:
    normalized = package_name.casefold().replace("-", "_")
    if normalized in BUILD_ENV_CONDA_ONLY:
        return "BUILD_ENV_CONDA_ONLY"
    return None


def parse_runtime_version(major: int, minor: int, build: int, revision: int = 0) -> tuple[int, ...]:
    """Normalize the VC Redistributable registry fields for policy comparisons."""
    values = (major, minor, build, revision)
    if any(not isinstance(value, int) or value < 0 for value in values):
        raise ValueError("VC runtime version fields must be non-negative integers")
    return values


def minimum_runtime_version(contract: dict[str, object]) -> tuple[int, ...]:
    raw = contract.get("minimum_version")
    if not isinstance(raw, str) or not re.fullmatch(r"\d+(?:\.\d+){2,3}", raw):
        raise ValueError("VC runtime prerequisite contract has an invalid minimum version")
    return tuple(int(part) for part in raw.split("."))


def version_below_minimum(minimum: tuple[int, ...]) -> tuple[int, ...]:
    """Return a valid non-negative version tuple strictly below the minimum."""
    values = list(minimum)
    for index in range(len(values) - 1, -1, -1):
        if values[index] > 0:
            values[index] -= 1
            return tuple(values)
    raise ValueError("VC runtime minimum must contain a positive version component")


def runtime_is_supported(
    *, installed: bool, architecture: str, version: tuple[int, ...], minimum: tuple[int, ...]
) -> bool:
    return installed and architecture.casefold() == "x64" and version >= minimum
