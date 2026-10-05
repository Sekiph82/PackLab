"""Studio-injected runtime resolution for portable Packaging Asset links."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

from packlab_core.packaging_asset import PackagingAsset


class ProjectRootResolver(Protocol):
    """Resolve a stable project ID to its current local root, if available."""

    def __call__(self, project_id: str) -> Path | None: ...


class ProjectRootAvailability(StrEnum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class RuntimeProjectRootResolution:
    """Transient Studio result; the root is never copied into canonical library data."""

    project_id: str
    availability: ProjectRootAvailability
    project_root: Path | None

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("packaging_asset_project_id_invalid")
        if not isinstance(self.availability, ProjectRootAvailability):
            raise ValueError("packaging_asset_project_availability_invalid")
        if self.availability is ProjectRootAvailability.AVAILABLE:
            if not isinstance(self.project_root, Path):
                raise ValueError("packaging_asset_project_root_required")
        elif self.project_root is not None:
            raise ValueError("packaging_asset_unavailable_project_root_forbidden")


def resolve_packaging_asset_project_roots(
    asset: PackagingAsset, resolver: ProjectRootResolver
) -> tuple[RuntimeProjectRootResolution, ...]:
    """Resolve exact linked project IDs through Studio's injected local resolver."""
    if not isinstance(asset, PackagingAsset):
        raise ValueError("packaging_asset_required")
    if not callable(resolver):
        raise ValueError("packaging_asset_project_resolver_required")

    project_ids = {item.project_id for item in asset.raw_scan_links}
    project_ids.update(item.project_id for item in asset.design_model_links)
    if asset.scan_master_link is not None:
        project_ids.add(asset.scan_master_link.project_id)

    resolved: list[RuntimeProjectRootResolution] = []
    for project_id in sorted(project_ids):
        root = resolver(project_id)
        if root is None:
            resolved.append(
                RuntimeProjectRootResolution(project_id, ProjectRootAvailability.UNAVAILABLE, None)
            )
        elif isinstance(root, Path):
            resolved.append(
                RuntimeProjectRootResolution(project_id, ProjectRootAvailability.AVAILABLE, root)
            )
        else:
            raise ValueError("packaging_asset_project_root_invalid")
    return tuple(resolved)


__all__ = [
    "ProjectRootAvailability",
    "RuntimeProjectRootResolution",
    "resolve_packaging_asset_project_roots",
]
