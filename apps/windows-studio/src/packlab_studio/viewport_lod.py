"""Deterministic interactive display budgets for M06 viewport scenes."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .viewport import Geometry, MeshGeometry, PointCloudGeometry


@dataclass(frozen=True, slots=True)
class LODPlan:
    source_count: int
    display_count: int
    stride: int
    budget: int
    level: str
    decimation: str

    def to_dict(self) -> dict[str, object]:
        return {
            "source_count": self.source_count,
            "display_count": self.display_count,
            "stride": self.stride,
            "budget": self.budget,
            "level": self.level,
            "decimation": self.decimation,
        }


@dataclass(frozen=True, slots=True)
class LODPolicy:
    display_budget: int = 50_000
    decimation_available: bool = True

    def plan(self, source_count: int) -> LODPlan:
        if source_count < 0:
            raise ValueError("source count cannot be negative")
        if source_count <= self.display_budget or not self.decimation_available:
            return LODPlan(
                source_count,
                source_count,
                1,
                self.display_budget,
                "full" if source_count <= self.display_budget else "fallback-full",
                "none" if source_count <= self.display_budget else "fallback-no-decimator",
            )
        stride = max(1, math.ceil(source_count / self.display_budget))
        return LODPlan(
            source_count,
            math.ceil(source_count / stride),
            stride,
            self.display_budget,
            "budgeted",
            "deterministic-stride",
        )


def geometry_count(geometry: Geometry) -> int:
    return len(geometry.points) if isinstance(geometry, PointCloudGeometry) else len(geometry.triangles)


def display_geometry(geometry: Geometry, policy: LODPolicy) -> tuple[Geometry, LODPlan]:
    """Return an immutable display representation and leave source geometry untouched."""

    source_count = geometry_count(geometry)
    plan = policy.plan(source_count)
    if plan.stride == 1:
        return geometry, plan
    if isinstance(geometry, PointCloudGeometry):
        return PointCloudGeometry(geometry.points[:: plan.stride]), plan
    triangles = geometry.triangles[:: plan.stride]
    used = sorted({index for triangle in triangles for index in triangle})
    remap = {old: new for new, old in enumerate(used)}
    vertices = tuple(geometry.vertices[index] for index in used)
    mapped: tuple[tuple[int, int, int], ...] = tuple(
        tuple(remap[index] for index in triangle) for triangle in triangles  # type: ignore[misc]
    )
    normals = tuple(geometry.normals[index] for index in used) if geometry.normals else ()
    return MeshGeometry(vertices, mapped, normals), plan
