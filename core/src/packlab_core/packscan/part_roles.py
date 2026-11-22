"""Scan part roles (PL-0482/PL-0489): which part of the package one PackScan shows.

The manifest field ``part_role`` is optional; packages without it are ``assembled``
(every package captured before PL-0482 showed the whole, lid-on package).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

PART_ROLES = (
    "closure",
    "closure_flipped",
    "body",
    "body_flipped",
    "assembled",
    "assembled_flipped",
    "body_interior",
)
DEFAULT_PART_ROLE = "assembled"
# Part -> required views. Interior scans exist only for the open body (PL-0489); the
# closure inside comes from its flipped scan and the assembled part has no interior scan.
PART_VIEWS: dict[str, tuple[str, ...]] = {
    "closure": ("upright", "flipped"),
    "body": ("upright", "flipped", "interior"),
    "assembled": ("upright", "flipped"),
}
_VIEW_SUFFIX = {"upright": "", "flipped": "_flipped", "interior": "_interior"}


def is_part_role(value: object) -> bool:
    return isinstance(value, str) and value in PART_ROLES


def manifest_part_role(manifest: Mapping[str, object]) -> str:
    """Role declared by a validated manifest; absent means ``assembled``."""
    value = manifest.get("part_role", DEFAULT_PART_ROLE)
    if not is_part_role(value):
        raise ValueError("manifest part_role is not a known role")
    return str(value)


def parts_summary(roles: Iterable[str]) -> dict[str, dict[str, bool]]:
    """For each part, which of its views (upright/flipped/interior) have a scan."""
    present = set(roles)
    return {
        part: {view: f"{part}{_VIEW_SUFFIX[view]}" in present for view in views}
        for part, views in PART_VIEWS.items()
    }


__all__ = [
    "DEFAULT_PART_ROLE",
    "PART_ROLES",
    "PART_VIEWS",
    "is_part_role",
    "manifest_part_role",
    "parts_summary",
]
