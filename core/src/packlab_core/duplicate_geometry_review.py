"""Duplicate-geometry review: propose, never merge, shared physical packages across SKUs.

One physical package (same bottle, different label/artwork/colour) should be scanned once and
reused for every SKU that shares it. This module only *proposes* candidate groups. It never
merges, deletes, re-scales or upgrades any Scan Master or Design Model; reuse plans are built
exclusively from explicit owner/operator decision records.

Method: cheap pose-invariant screens (principal-frame extents, surface area, volume,
area-weighted radii of gyration, family) followed by rigid, proper-rotation-only alignment
(principal-axes initialisation + the pinned Open3D point-to-point ICP used by repeat-scan
registration; scaling is never enabled) and symmetric point-to-surface deviation. A pair that
only aligns after a reflection is reported as a mirror image (DISTINCT), never as a duplicate.
"""

from __future__ import annotations

import bisect
import hashlib
import itertools
import json
import math
import random
import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from .coordinate_frame import coordinate_unit_for_scale_state
from .design_model import DesignModelRevision, PackageFamily
from .design_preview import DesignPreview
from .geometry_adapter import (
    GeometryAdapterError,
    Open3DGeometryAdapter,
    PointCloudData,
    TriangleMeshData,
)
from .reconstruction import ScaleState

# Package-internal reuse of the rigid-transform gate (orthonormal, det +1, no scale). It is a
# private name in repeat_scan_registration; if that module renames it this import breaks loudly.
from .repeat_scan_registration import (
    RegistrationError,
    RegistrationPolicy,
    _validate_rigid_transform,
)
from .scan_master import ScanMasterRevision, mesh_sha256

REPORT_CONTRACT = "packlab.duplicate-geometry-review.v1"
PLAN_CONTRACT = "packlab.duplicate-geometry-reuse-plan.v1"
PHYSICAL_EVIDENCE_PENDING = "PHYSICAL_EVIDENCE_PENDING"
HARD_MAX_ENTRIES = 256
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_MAX_VERTICES = 200_000
_MAX_TRIANGLES = 400_000
UNVERIFIED_PROVENANCE = "CALLER_ASSERTED_UNVERIFIED"
# ICP target clouds are denser than the source/query samples: point-to-point ICP bias shrinks
# with target spacing. ponytail: point-to-plane refinement would remove the bias entirely.
_TARGET_DENSITY = 12

Vec = tuple[float, float, float]
Mat = tuple[Vec, Vec, Vec]


class DuplicateGeometryError(ValueError):
    """Raised when a review input is unsafe; the review fails closed."""


class AuthorityKind(StrEnum):
    SCAN_MASTER = "SCAN_MASTER"
    DESIGN_MODEL = "DESIGN_MODEL"


class ReviewDecision(StrEnum):
    PROPOSED_DUPLICATE = "PROPOSED_DUPLICATE"
    DISTINCT = "DISTINCT"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise DuplicateGeometryError(f"{name}_invalid")
    return value


def _hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class LibraryGeometryEntry:
    """One library geometry (Scan Master mesh or Design Model tessellation) bound to SKUs."""

    entry_id: str
    authority_kind: AuthorityKind
    authority_revision_id: str
    family: PackageFamily
    sku_ids: tuple[str, ...]
    scale_state: ScaleState | None
    coordinate_unit: str | None
    mesh: TriangleMeshData
    coverage_fraction: float
    simulation_only: bool
    # Only the from_scan_master / from_design_model factories set a verified provenance; a
    # directly constructed (or dataclasses.replace'd) entry is always caller-asserted.
    geometry_provenance: str = field(init=False, default=UNVERIFIED_PROVENANCE)

    def __post_init__(self) -> None:
        _identifier(self.entry_id, "entry_id")
        if not isinstance(self.authority_kind, AuthorityKind):
            raise DuplicateGeometryError("authority_kind_invalid")
        if not isinstance(self.authority_revision_id, str) or not self.authority_revision_id:
            raise DuplicateGeometryError("authority_revision_id_invalid")
        if not isinstance(self.family, PackageFamily):
            raise DuplicateGeometryError("family_invalid")
        if not isinstance(self.sku_ids, tuple) or not self.sku_ids:
            raise DuplicateGeometryError("sku_ids_required")
        for sku in self.sku_ids:
            _identifier(sku, "sku_id")
        if len(set(self.sku_ids)) != len(self.sku_ids):
            raise DuplicateGeometryError("sku_ids_duplicate")
        object.__setattr__(self, "sku_ids", tuple(sorted(self.sku_ids)))
        if self.scale_state is not None and not isinstance(self.scale_state, ScaleState):
            raise DuplicateGeometryError("scale_state_invalid")
        if not isinstance(self.mesh, TriangleMeshData):
            raise DuplicateGeometryError("mesh_required")
        if len(self.mesh.vertices) < 4 or len(self.mesh.triangles) < 4:
            raise DuplicateGeometryError("mesh_too_small")
        if len(self.mesh.vertices) > _MAX_VERTICES:
            raise DuplicateGeometryError("mesh_vertex_bound_exceeded")
        if len(self.mesh.triangles) > _MAX_TRIANGLES:
            raise DuplicateGeometryError("mesh_triangle_bound_exceeded")
        if any(not math.isfinite(c) for v in self.mesh.vertices for c in v):
            raise DuplicateGeometryError("geometry_non_finite")
        if (
            isinstance(self.coverage_fraction, bool)
            or not isinstance(self.coverage_fraction, (int, float))
            or not math.isfinite(self.coverage_fraction)
            or not 0.0 < self.coverage_fraction <= 1.0
        ):
            raise DuplicateGeometryError("coverage_fraction_invalid")
        if not isinstance(self.simulation_only, bool):
            raise DuplicateGeometryError("simulation_only_must_be_bool")

    @property
    def geometry_sha256(self) -> str:
        return mesh_sha256(self.mesh)

    @property
    def authority_verified(self) -> bool:
        return self.geometry_provenance != UNVERIFIED_PROVENANCE

    def _verified(self, provenance: str) -> LibraryGeometryEntry:
        object.__setattr__(self, "geometry_provenance", provenance)
        return self

    @classmethod
    def from_scan_master(
        cls,
        revision: ScanMasterRevision,
        *,
        entry_id: str,
        family: PackageFamily,
        sku_ids: tuple[str, ...],
        coverage_fraction: float,
        simulation_only: bool,
    ) -> LibraryGeometryEntry:
        manifest = revision.manifest
        if (
            manifest.get("authority_class") != "SCAN_MASTER"
            or manifest.get("scan_master_revision_id") != revision.revision_id
            or manifest.get("output_geometry_sha256") != mesh_sha256(revision.mesh)
        ):
            raise DuplicateGeometryError("scan_master_manifest_invalid")
        raw_state = manifest.get("scale_state")
        try:
            state = ScaleState(raw_state) if isinstance(raw_state, str) else None
        except ValueError as error:
            raise DuplicateGeometryError("scale_state_invalid") from error
        return cls(
            entry_id,
            AuthorityKind.SCAN_MASTER,
            revision.revision_id,
            family,
            sku_ids,
            state,
            None if state is None else coordinate_unit_for_scale_state(state),
            revision.mesh,
            coverage_fraction,
            simulation_only,
        )._verified("SCAN_MASTER_MANIFEST_DIGEST")

    @classmethod
    def from_design_model(
        cls,
        revision: DesignModelRevision,
        preview: DesignPreview,
        *,
        entry_id: str,
        sku_ids: tuple[str, ...],
        simulation_only: bool,
    ) -> LibraryGeometryEntry:
        """Use a Design Preview tessellation whose lineage is bound to this exact revision."""

        if not isinstance(revision, DesignModelRevision) or not isinstance(preview, DesignPreview):
            raise DuplicateGeometryError("design_model_and_preview_required")
        root = revision.standalone_root
        if (
            preview.model_revision_id != revision.revision_id
            or preview.scale_state is not revision.scale_state
            or preview.coordinate_unit != revision.coordinate_unit
            or preview.standalone_root_revision_id != (None if root is None else root.revision_id)
            or preview.scan_master_revision_id != revision.fitted_to_scan_master_revision_id
            or preview.scan_master_geometry_sha256 != revision.scan_master_geometry_sha256
            or preview.parent_binding_revision_id != revision.parent_binding_revision_id
        ):
            raise DuplicateGeometryError("design_preview_not_bound_to_revision")
        return cls(
            entry_id,
            AuthorityKind.DESIGN_MODEL,
            revision.revision_id,
            revision.package_family,
            sku_ids,
            revision.scale_state,
            revision.coordinate_unit,
            preview.mesh,
            1.0,
            simulation_only,
        )._verified("DESIGN_PREVIEW_BOUND_TO_REVISION")

    def summary(self) -> dict[str, object]:
        return {
            "entry_id": self.entry_id,
            "authority_kind": self.authority_kind.value,
            "authority_revision_id": self.authority_revision_id,
            "geometry_sha256": self.geometry_sha256,
            "geometry_provenance": self.geometry_provenance,
            "authority_verified": self.authority_verified,
            "family": self.family.value,
            "sku_ids": list(self.sku_ids),
            "coverage_fraction": float(self.coverage_fraction),
            "simulation_only": self.simulation_only,
        }


@dataclass(frozen=True, slots=True)
class DuplicateReviewPolicy:
    """Tolerances are in the entries' shared coordinate unit (mm or mm_unverified)."""

    max_entries: int = 64
    invariant_relative_tolerance: float = 0.01
    extent_absolute_tolerance: float = 0.5
    rms_tolerance: float = 0.25
    max_deviation_tolerance: float = 0.75
    review_rms_tolerance: float = 0.6
    min_coverage_fraction: float = 0.98
    sample_points: int = 1500
    registration: RegistrationPolicy = field(
        default_factory=lambda: RegistrationPolicy(
            maximum_correspondence_distance=5.0, maximum_iterations=60, maximum_inlier_rmse=1.0
        )
    )

    def __post_init__(self) -> None:
        if (
            isinstance(self.max_entries, bool)
            or not isinstance(self.max_entries, int)
            or not 2 <= self.max_entries <= HARD_MAX_ENTRIES
        ):
            raise DuplicateGeometryError("max_entries_invalid")
        for name in (
            "invariant_relative_tolerance",
            "extent_absolute_tolerance",
            "rms_tolerance",
            "max_deviation_tolerance",
            "review_rms_tolerance",
            "min_coverage_fraction",
        ):
            value = getattr(self, name)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                raise DuplicateGeometryError(f"{name}_invalid")
        if self.review_rms_tolerance < self.rms_tolerance or self.min_coverage_fraction > 1:
            raise DuplicateGeometryError("policy_tolerances_inconsistent")
        if not isinstance(self.registration, RegistrationPolicy):
            raise DuplicateGeometryError("registration_policy_invalid")
        if (
            isinstance(self.sample_points, bool)
            or not isinstance(self.sample_points, int)
            or self.sample_points < 100
            or self.sample_points * _TARGET_DENSITY > self.registration.maximum_points_per_revision
        ):
            raise DuplicateGeometryError("sample_points_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "max_entries": self.max_entries,
            "invariant_relative_tolerance": float(self.invariant_relative_tolerance),
            "extent_absolute_tolerance": float(self.extent_absolute_tolerance),
            "rms_tolerance": float(self.rms_tolerance),
            "max_deviation_tolerance": float(self.max_deviation_tolerance),
            "review_rms_tolerance": float(self.review_rms_tolerance),
            "min_coverage_fraction": float(self.min_coverage_fraction),
            "sample_points": self.sample_points,
            # Only the ICP parameters actually used; the RegistrationPolicy inlier gates
            # (minimum_fitness/inlier count/inlier RMSE) are not applied here. The
            # point-to-surface deviation gates above are the acceptance criteria.
            "registration": {
                "algorithm": "open3d_point_to_point_icp_rigid_v1",
                "maximum_correspondence_distance": float(
                    self.registration.maximum_correspondence_distance
                ),
                "maximum_iterations": self.registration.maximum_iterations,
                "relative_fitness_tolerance": float(self.registration.relative_fitness_tolerance),
                "relative_rmse_tolerance": float(self.registration.relative_rmse_tolerance),
                "maximum_points_per_revision": self.registration.maximum_points_per_revision,
                "scaling_enabled": False,
            },
        }


# ---------------------------------------------------------------- small linear algebra


def _matmul(a: Mat, b: Mat) -> Mat:
    rows = [tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)) for i in range(3)]
    return (rows[0], rows[1], rows[2])  # type: ignore[return-value]


def _transpose(a: Mat) -> Mat:
    return ((a[0][0], a[1][0], a[2][0]), (a[0][1], a[1][1], a[2][1]), (a[0][2], a[1][2], a[2][2]))


def _det(a: Mat) -> float:
    return (
        a[0][0] * (a[1][1] * a[2][2] - a[1][2] * a[2][1])
        - a[0][1] * (a[1][0] * a[2][2] - a[1][2] * a[2][0])
        + a[0][2] * (a[1][0] * a[2][1] - a[1][1] * a[2][0])
    )


def _apply(r: Mat, t: Vec, p: Vec) -> Vec:
    return (
        r[0][0] * p[0] + r[0][1] * p[1] + r[0][2] * p[2] + t[0],
        r[1][0] * p[0] + r[1][1] * p[1] + r[1][2] * p[2] + t[1],
        r[2][0] * p[0] + r[2][1] * p[1] + r[2][2] * p[2] + t[2],
    )


def _split(transform: tuple[float, ...]) -> tuple[Mat, Vec]:
    r = tuple(tuple(transform[row * 4 + col] for col in range(3)) for row in range(3))
    return r, (transform[3], transform[7], transform[11])  # type: ignore[return-value]


def _join(r: Mat, t: Vec) -> tuple[float, ...]:
    return (*r[0], t[0], *r[1], t[1], *r[2], t[2], 0.0, 0.0, 0.0, 1.0)


def _symmetric_eigen(m: list[list[float]]) -> tuple[list[float], Mat]:
    """Cyclic Jacobi; returns descending eigenvalues and a right-handed eigenvector basis."""

    a = [row[:] for row in m]
    v = [[1.0 if i == j else 0.0 for j in range(3)] for i in range(3)]
    for _sweep in range(60):
        off = sum(a[i][j] ** 2 for i in range(3) for j in range(3) if i != j)
        if off < 1e-30 * max(1.0, sum(a[i][i] ** 2 for i in range(3))):
            break
        for p, q in ((0, 1), (0, 2), (1, 2)):
            if abs(a[p][q]) < 1e-300:
                continue
            theta = (a[q][q] - a[p][p]) / (2.0 * a[p][q])
            t = math.copysign(1.0, theta) / (abs(theta) + math.sqrt(theta * theta + 1.0))
            c = 1.0 / math.sqrt(t * t + 1.0)
            s = t * c
            for k in range(3):
                akp, akq = a[k][p], a[k][q]
                a[k][p], a[k][q] = c * akp - s * akq, s * akp + c * akq
            for k in range(3):
                apk, aqk = a[p][k], a[q][k]
                a[p][k], a[q][k] = c * apk - s * aqk, s * apk + c * aqk
            for k in range(3):
                vkp, vkq = v[k][p], v[k][q]
                v[k][p], v[k][q] = c * vkp - s * vkq, s * vkp + c * vkq
    order = sorted(range(3), key=lambda i: -a[i][i])
    values = [a[i][i] for i in order]
    cols = [[v[k][i] for k in range(3)] for i in order]
    basis: Mat = _transpose((tuple(cols[0]), tuple(cols[1]), tuple(cols[2])))  # type: ignore[arg-type]
    if _det(basis) < 0:
        cols[2] = [-x for x in cols[2]]
        basis = _transpose((tuple(cols[0]), tuple(cols[1]), tuple(cols[2])))  # type: ignore[arg-type]
    return values, basis


# ---------------------------------------------------------------- per-entry invariants


@dataclass(frozen=True, slots=True)
class _Prepared:
    entry: LibraryGeometryEntry
    mesh: TriangleMeshData
    centroid: Vec
    axes: Mat
    extents: tuple[float, float, float]
    gyration: tuple[float, float, float]
    area: float
    volume: float | None
    boundary_edges: int
    partial: bool
    samples: tuple[Vec, ...]  # dense ICP target cloud; the prefix is the query/source sample

    @property
    def queries(self) -> tuple[Vec, ...]:
        return self.samples[: len(self.samples) // _TARGET_DENSITY]

    def invariants(self) -> dict[str, Any]:
        return {
            "principal_extents_sorted": [round(x, 6) for x in self.extents],
            "radii_of_gyration_sorted": [round(x, 6) for x in self.gyration],
            "surface_area": round(self.area, 6),
            "enclosed_volume": None if self.volume is None else round(self.volume, 6),
            "boundary_edge_count": self.boundary_edges,
            "partial_coverage": self.partial,
        }


def _prepare(
    entry: LibraryGeometryEntry, policy: DuplicateReviewPolicy, mesh: TriangleMeshData
) -> _Prepared:
    vertices = mesh.vertices
    areas: list[float] = []
    second = [[0.0] * 3 for _ in range(3)]
    first = [0.0, 0.0, 0.0]
    volume6 = 0.0
    edges: dict[tuple[int, int], int] = {}
    for i, j, k in mesh.triangles:
        a, b, c = vertices[i], vertices[j], vertices[k]
        u = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        w = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        cross = (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])
        area = 0.5 * math.sqrt(sum(x * x for x in cross))
        areas.append(area)
        s = (a[0] + b[0] + c[0], a[1] + b[1] + c[1], a[2] + b[2] + c[2])
        for r in range(3):
            first[r] += area * s[r] / 3.0
            for col in range(3):
                second[r][col] += (
                    area / 12.0 * (a[r] * a[col] + b[r] * b[col] + c[r] * c[col] + s[r] * s[col])
                )
        volume6 += (
            a[0] * (b[1] * c[2] - b[2] * c[1])
            - a[1] * (b[0] * c[2] - b[2] * c[0])
            + a[2] * (b[0] * c[1] - b[1] * c[0])
        )
        for e in ((i, j), (j, k), (k, i)):
            key = (min(e), max(e))
            edges[key] = edges.get(key, 0) + 1
    total = sum(areas)
    if not math.isfinite(total) or total <= 0:
        raise DuplicateGeometryError("geometry_degenerate")
    centroid: Vec = (first[0] / total, first[1] / total, first[2] / total)
    covariance = [
        [second[r][col] / total - centroid[r] * centroid[col] for col in range(3)] for r in range(3)
    ]
    values, axes = _symmetric_eigen(covariance)
    projected = [
        tuple(sum(axes[r][col] * (p[r] - centroid[r]) for r in range(3)) for col in range(3))
        for p in vertices
    ]
    extents = tuple(
        sorted(max(p[c] for p in projected) - min(p[c] for p in projected) for c in range(3))
    )
    boundary = sum(1 for count in edges.values() if count != 2)
    partial = boundary > 0 or entry.coverage_fraction < policy.min_coverage_fraction
    # Deterministic area-weighted surface samples make the comparison tessellation-independent.
    rng = random.Random(int(mesh_sha256(mesh)[:16], 16))
    cumulative = list(itertools.accumulate(areas))
    samples: list[Vec] = []
    for _ in range(policy.sample_points * _TARGET_DENSITY):
        index = min(bisect.bisect_left(cumulative, rng.random() * total), len(areas) - 1)
        i, j, k = mesh.triangles[index]
        a, b, c = vertices[i], vertices[j], vertices[k]
        r1, r2 = math.sqrt(rng.random()), rng.random()
        wa, wb, wc = 1 - r1, r1 * (1 - r2), r1 * r2
        samples.append(
            (
                wa * a[0] + wb * b[0] + wc * c[0],
                wa * a[1] + wb * b[1] + wc * c[1],
                wa * a[2] + wb * b[2] + wc * c[2],
            )
        )
    return _Prepared(
        entry,
        mesh,
        centroid,
        axes,
        (extents[0], extents[1], extents[2]),
        tuple(sorted(math.sqrt(max(x, 0.0)) for x in values)),  # type: ignore[arg-type]
        total,
        None if partial else abs(volume6) / 6.0,
        boundary,
        partial,
        tuple(samples),
    )


def _mirror(mesh: TriangleMeshData) -> TriangleMeshData:
    return TriangleMeshData(
        tuple((-x, y, z) for x, y, z in mesh.vertices),
        tuple((i, k, j) for i, j, k in mesh.triangles),
    )


def _invariant_reasons(a: _Prepared, b: _Prepared, policy: DuplicateReviewPolicy) -> list[str]:
    rel = policy.invariant_relative_tolerance

    def differs(x: float, y: float, floor: float = 0.0) -> bool:
        return abs(x - y) > max(floor, rel * max(abs(x), abs(y)))

    reasons: list[str] = []
    if a.partial or b.partial:
        # Sound necessary condition only: any width of a subset is at most the subset diameter,
        # which is at most the parent diameter <= norm of the parent's orthogonal extents.
        # (Comparing sorted PCA extents is NOT sound: a subset's principal frame can rotate.)
        small, large = (a, b) if a.partial else (b, a)
        diameter = math.sqrt(sum(x * x for x in large.extents))
        if not (a.partial and b.partial) and max(small.extents) > diameter + max(
            policy.extent_absolute_tolerance, rel * diameter
        ):
            reasons.append("partial_larger_than_complete_geometry_diameter")
        return reasons
    if any(
        differs(x, y, policy.extent_absolute_tolerance)
        for x, y in zip(a.extents, b.extents, strict=True)
    ):
        reasons.append("extent_mismatch")
    if any(
        differs(x, y, policy.extent_absolute_tolerance)
        for x, y in zip(a.gyration, b.gyration, strict=True)
    ):
        reasons.append("principal_axes_signature_mismatch")
    if differs(a.area, b.area):
        reasons.append("surface_area_mismatch")
    if a.volume is not None and b.volume is not None and differs(a.volume, b.volume):
        reasons.append("volume_mismatch")
    return reasons


_CANDIDATE_TURNS: tuple[Mat, ...] = tuple(
    _matmul(((sx, 0.0, 0.0), (0.0, sy, 0.0), (0.0, 0.0, sx * sy)), turn)
    for sx, sy in ((1.0, 1.0), (1.0, -1.0), (-1.0, 1.0), (-1.0, -1.0))
    for turn in (
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        ((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)),
    )
)


def _evaluate(
    source: _Prepared,
    target: _Prepared,
    transform: tuple[float, ...],
    fitness: float,
    adapter: Open3DGeometryAdapter,
) -> dict[str, Any]:
    """Symmetric point-to-surface deviation of query samples under a proper rigid transform."""

    # Rejects reflection and scale: only proper rigid motions are admissible.
    _validate_rigid_transform(transform, "registration_transform")
    r, t = _split(transform)
    forward = adapter.compute_mesh_surface_distances(
        target.mesh,
        PointCloudData(points=tuple(_apply(r, t, p) for p in source.queries)),
        signed=False,
    ).distances
    rt = _transpose(r)
    back = _apply(rt, (0.0, 0.0, 0.0), t)
    reverse = adapter.compute_mesh_surface_distances(
        source.mesh,
        PointCloudData(
            points=tuple(_apply(rt, (-back[0], -back[1], -back[2]), p) for p in target.queries)
        ),
        signed=False,
    ).distances
    both = tuple(forward) + tuple(reverse)
    if not both or any(not math.isfinite(d) for d in both):
        raise DuplicateGeometryError("surface_distance_non_finite")
    return {
        "rms_deviation": round(math.sqrt(sum(d * d for d in both) / len(both)), 6),
        "max_deviation": round(max(both), 6),
        "forward_rms": round(math.sqrt(sum(d * d for d in forward) / len(forward)), 6),
        "reverse_rms": round(math.sqrt(sum(d * d for d in reverse) / len(reverse)), 6),
        "transform_source_to_target": [round(x, 9) for x in transform],
        "icp_fitness": round(fitness, 6),
    }


def _align(
    source: _Prepared,
    target: _Prepared,
    policy: DuplicateReviewPolicy,
    adapter: Open3DGeometryAdapter,
) -> dict[str, Any]:
    """Best proper-rotation rigid fit of source onto target, scored by symmetric surface RMS.

    Coarse: multi-start ICP on the sparse query clouds from 8 proper principal-axes poses.
    Fine: one ICP on the dense clouds from the best coarse pose.
    """

    reg = policy.registration

    def icp(src: tuple[Vec, ...], dst: tuple[Vec, ...], initial: tuple[float, ...]):
        _validate_rigid_transform(initial, "initial_transform")
        return adapter.register_point_clouds(
            PointCloudData(points=src),
            PointCloudData(points=dst),
            initial_transform=initial,
            maximum_correspondence_distance=reg.maximum_correspondence_distance,
            relative_fitness=reg.relative_fitness_tolerance,
            relative_rmse=reg.relative_rmse_tolerance,
            maximum_iterations=reg.maximum_iterations,
        )

    best: dict[str, Any] | None = None
    for turn in _CANDIDATE_TURNS:
        rotation = _matmul(_matmul(target.axes, turn), _transpose(source.axes))
        moved = _apply(rotation, (0.0, 0.0, 0.0), source.centroid)
        translation: Vec = (
            target.centroid[0] - moved[0],
            target.centroid[1] - moved[1],
            target.centroid[2] - moved[2],
        )
        output = icp(source.queries, target.queries, _join(rotation, translation))
        fit = _evaluate(source, target, output.transformation, output.fitness, adapter)
        if best is None or (fit["rms_deviation"], fit["max_deviation"]) < (
            best["rms_deviation"],
            best["max_deviation"],
        ):
            best = fit
    assert best is not None
    refined = icp(source.samples, target.samples, tuple(best["transform_source_to_target"]))
    fine = _evaluate(source, target, refined.transformation, refined.fitness, adapter)
    if (fine["rms_deviation"], fine["max_deviation"]) <= (
        best["rms_deviation"],
        best["max_deviation"],
    ):
        return fine
    return best


def _fits(fit: dict[str, Any], policy: DuplicateReviewPolicy) -> bool:
    rms, peak = fit["rms_deviation"], fit["max_deviation"]
    assert isinstance(rms, float) and isinstance(peak, float)
    return rms <= policy.rms_tolerance and peak <= policy.max_deviation_tolerance


def _compare(
    a: _Prepared,
    b: _Prepared,
    policy: DuplicateReviewPolicy,
    adapter: Open3DGeometryAdapter,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "entry_ids": [a.entry.entry_id, b.entry.entry_id],
        "registration": None,
        "mirror_registration": None,
    }
    reasons = _invariant_reasons(a, b, policy)
    if a.partial or b.partial:
        if reasons:
            decision = ReviewDecision.DISTINCT
        else:
            decision = ReviewDecision.NEEDS_HUMAN_REVIEW
            reasons = ["partial_coverage_cannot_confirm_duplicate"]
        return record | {"decision": decision.value, "reasons": reasons}
    if reasons:
        return record | {"decision": ReviewDecision.DISTINCT.value, "reasons": reasons}
    fit = _align(a, b, policy, adapter)
    record["registration"] = fit
    if _fits(fit, policy):
        return record | {
            "decision": ReviewDecision.PROPOSED_DUPLICATE.value,
            "reasons": ["invariants_and_rigid_deviation_within_tolerance"],
        }
    # Proper-rotation fit failed: check whether only a reflection makes them coincide.
    mirrored = _prepare(a.entry, policy, _mirror(a.mesh))
    mirror_fit = _align(mirrored, b, policy, adapter)
    record["mirror_registration"] = mirror_fit
    # Mirror reason only when the reflected fit is good AND the proper fit is clearly worse;
    # otherwise a poor ICP basin on an achiral shape could be mislabelled as handedness.
    proper_rms, mirror_rms = fit["rms_deviation"], mirror_fit["rms_deviation"]
    if (
        _fits(mirror_fit, policy)
        and proper_rms > policy.review_rms_tolerance
        and proper_rms >= 4.0 * mirror_rms
    ):
        return record | {
            "decision": ReviewDecision.DISTINCT.value,
            "reasons": ["mirror_image_handedness_differs"],
        }
    rms = fit["rms_deviation"]
    assert isinstance(rms, float)
    if rms <= policy.review_rms_tolerance:
        return record | {
            "decision": ReviewDecision.NEEDS_HUMAN_REVIEW.value,
            "reasons": ["localized_deviation_exceeds_tolerance"],
        }
    return record | {
        "decision": ReviewDecision.DISTINCT.value,
        "reasons": ["rigid_deviation_exceeds_tolerance"],
    }


# ---------------------------------------------------------------- report


@dataclass(frozen=True, slots=True)
class DuplicateGeometryReview:
    """Immutable, digest-bound review report. Proposals only; nothing is merged."""

    canonical_json: bytes

    def as_dict(self) -> dict[str, Any]:
        value = json.loads(self.canonical_json)
        assert isinstance(value, dict)
        return value

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json).hexdigest()


def review_duplicate_geometry(
    entries: Sequence[LibraryGeometryEntry],
    *,
    policy: DuplicateReviewPolicy | None = None,
    adapter: Open3DGeometryAdapter | None = None,
) -> DuplicateGeometryReview:
    policy = DuplicateReviewPolicy() if policy is None else policy
    if not isinstance(policy, DuplicateReviewPolicy):
        raise DuplicateGeometryError("policy_invalid")
    entries = tuple(entries)
    if len(entries) > policy.max_entries:
        raise DuplicateGeometryError("entry_bound_exceeded")
    if len(entries) < 2 or any(not isinstance(e, LibraryGeometryEntry) for e in entries):
        raise DuplicateGeometryError("at_least_two_typed_entries_required")
    if len({e.entry_id for e in entries}) != len(entries):
        raise DuplicateGeometryError("entry_id_duplicate")
    states = {e.scale_state for e in entries}
    if None in states:
        raise DuplicateGeometryError("scale_state_missing")
    if len(states) != 1:
        raise DuplicateGeometryError("mixed_scale_states")
    state = entries[0].scale_state
    assert state is not None
    if state is ScaleState.RELATIVE:
        raise DuplicateGeometryError("relative_scale_forbidden")
    expected_unit = coordinate_unit_for_scale_state(state)
    if any(e.coordinate_unit != expected_unit for e in entries):
        raise DuplicateGeometryError("coordinate_unit_mismatch")
    backend = Open3DGeometryAdapter() if adapter is None else adapter
    ordered = sorted(entries, key=lambda e: e.entry_id)
    prepared = [_prepare(e, policy, e.mesh) for e in ordered]
    pairs: list[dict[str, Any]] = []
    try:
        for a, b in itertools.combinations(prepared, 2):
            if a.entry.family is b.entry.family:
                pairs.append(_compare(a, b, policy, backend))
    except (RegistrationError, GeometryAdapterError) as error:
        raise DuplicateGeometryError("registration_failed_closed") from error

    # Candidate groups: connected components over PROPOSED_DUPLICATE pairs. A component is only
    # PROPOSED_DUPLICATE when every member pair was independently confirmed (no transitive
    # merging). Each NEEDS_HUMAN_REVIEW pair outside such a component is its own review group.
    parent = {e.entry_id: e.entry_id for e in ordered}

    def root(x: str) -> str:
        while parent[x] != x:
            x = parent[x]
        return x

    for pair in pairs:
        if pair["decision"] == ReviewDecision.PROPOSED_DUPLICATE.value:
            left, right = pair["entry_ids"]
            parent[root(right)] = root(left)
    members: dict[str, list[str]] = {}
    for e in ordered:
        members.setdefault(root(e.entry_id), []).append(e.entry_id)
    candidates = [ids for ids in members.values() if len(ids) > 1]
    candidates += [
        list(p["entry_ids"])
        for p in pairs
        if p["decision"] == ReviewDecision.NEEDS_HUMAN_REVIEW.value
        and root(p["entry_ids"][0]) != root(p["entry_ids"][1])
    ]
    by_id = {e.entry_id: e for e in ordered}
    groups: list[dict[str, Any]] = []
    for ids in sorted(candidates):
        inside = [p for p in pairs if set(p["entry_ids"]) <= set(ids)]
        complete = len(inside) == len(ids) * (len(ids) - 1) // 2
        all_proposed = complete and all(
            p["decision"] == ReviewDecision.PROPOSED_DUPLICATE.value for p in inside
        )
        reasons = sorted({r for p in inside for r in p["reasons"]})
        if not all_proposed:
            reasons.append("group_not_fully_confirmed_pairwise")
        groups.append(
            {
                "group_id": "duplicate-group:" + _hash(sorted(ids)),
                "member_entry_ids": ids,
                "sku_ids": sorted({s for i in ids for s in by_id[i].sku_ids}),
                "decision": (
                    ReviewDecision.PROPOSED_DUPLICATE
                    if all_proposed
                    else ReviewDecision.NEEDS_HUMAN_REVIEW
                ).value,
                "reasons": reasons,
                "pairs": inside,
                "requires_owner_decision_record": True,
            }
        )
    body = {
        "contract": REPORT_CONTRACT,
        "version": 1,
        "scale_state": state.value,
        "coordinate_unit": expected_unit,
        "policy": policy.as_dict(),
        "entries": [
            by_id[p.entry.entry_id].summary() | {"invariants": p.invariants()} for p in prepared
        ],
        "pairs": pairs,
        "groups": groups,
        "simulation_only": any(e.simulation_only for e in ordered),
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
        "auto_merge_performed": False,
        "deletion_performed": False,
        "authority_changes": "NONE",
    }
    return DuplicateGeometryReview(
        json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    )


# ---------------------------------------------------------------- decisions and reuse plan


@dataclass(frozen=True, slots=True)
class DuplicateDecisionRecord:
    review_sha256: str
    group_id: str
    decision: str  # "APPROVE" | "REJECT"
    actor_id: str
    decided_at_utc: str
    reason: str
    canonical_entry_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.review_sha256, str) or not _SHA256.fullmatch(self.review_sha256):
            raise DuplicateGeometryError("decision_review_sha256_invalid")
        if not isinstance(self.group_id, str) or not self.group_id.startswith("duplicate-group:"):
            raise DuplicateGeometryError("decision_group_id_invalid")
        if self.decision not in {"APPROVE", "REJECT"}:
            raise DuplicateGeometryError("decision_invalid")
        _identifier(self.actor_id, "decision_actor_id")
        if not isinstance(self.decided_at_utc, str) or not _UTC.fullmatch(self.decided_at_utc):
            raise DuplicateGeometryError("decision_timestamp_invalid")
        if not isinstance(self.reason, str) or not self.reason.strip() or len(self.reason) > 1000:
            raise DuplicateGeometryError("decision_reason_invalid")
        if (self.decision == "APPROVE") != (self.canonical_entry_id is not None):
            raise DuplicateGeometryError("canonical_entry_required_only_for_approval")


def build_reuse_plan(
    review: DuplicateGeometryReview, records: Iterable[DuplicateDecisionRecord]
) -> dict[str, Any]:
    """'Scan once, reuse for SKUs X, Y, Z' from approved records only. Changes no authority."""

    if not isinstance(review, DuplicateGeometryReview):
        raise DuplicateGeometryError("review_required")
    report = review.as_dict()
    if report.get("contract") != REPORT_CONTRACT or report.get("version") != 1:
        raise DuplicateGeometryError("review_contract_or_version_unsupported")
    groups = {g["group_id"]: g for g in report["groups"]}
    entries = {e["entry_id"]: e for e in report["entries"]}
    seen: set[str] = set()
    claimed: set[str] = set()
    approved: list[dict[str, Any]] = []
    rejected: list[str] = []
    for record in records:
        if not isinstance(record, DuplicateDecisionRecord):
            raise DuplicateGeometryError("decision_record_invalid")
        if record.review_sha256 != review.sha256:
            raise DuplicateGeometryError("decision_review_digest_mismatch")
        if record.group_id not in groups:
            raise DuplicateGeometryError("decision_group_unknown")
        if record.group_id in seen:
            raise DuplicateGeometryError("decision_group_conflict")
        seen.add(record.group_id)
        if record.decision == "REJECT":
            rejected.append(record.group_id)
            continue
        group = groups[record.group_id]
        if record.canonical_entry_id not in group["member_entry_ids"]:
            raise DuplicateGeometryError("canonical_entry_not_group_member")
        if claimed & set(group["member_entry_ids"]):
            raise DuplicateGeometryError("approved_groups_overlap")
        claimed |= set(group["member_entry_ids"])
        canonical = entries[record.canonical_entry_id]
        if canonical["invariants"]["partial_coverage"]:
            raise DuplicateGeometryError("canonical_entry_partial_coverage")
        if canonical["authority_verified"] is not True:
            raise DuplicateGeometryError("canonical_entry_authority_unverified")
        # A component that contains any DISTINCT pair (including mirror images) is not one
        # physical package; it cannot be approved for reuse as a whole.
        if any(p["decision"] == ReviewDecision.DISTINCT.value for p in group["pairs"]):
            raise DuplicateGeometryError("approval_blocked_distinct_pair_in_group")
        approved.append(
            {
                "group_id": record.group_id,
                "review_decision": group["decision"],
                "scan_once_entry_id": record.canonical_entry_id,
                "scan_once_authority_kind": canonical["authority_kind"],
                "scan_once_authority_revision_id": canonical["authority_revision_id"],
                "scan_once_geometry_provenance": canonical["geometry_provenance"],
                "scan_once_geometry_sha256": canonical["geometry_sha256"],
                "reuse_for_sku_ids": group["sku_ids"],
                "member_entry_ids": group["member_entry_ids"],
                "approved_by": record.actor_id,
                "approved_at_utc": record.decided_at_utc,
                "approval_reason": record.reason,
            }
        )
    body = {
        "contract": PLAN_CONTRACT,
        "version": 1,
        "review_sha256": review.sha256,
        "approved_reuse": sorted(approved, key=lambda item: str(item["group_id"])),
        "rejected_group_ids": sorted(rejected),
        "undecided_group_ids": sorted(set(groups) - seen),
        "authority_changes": "NONE",
        "existing_scan_master_authority_preserved": True,
        "auto_merge_performed": False,
        "deletion_performed": False,
        "simulation_only": report["simulation_only"],
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
    }
    return body | {"plan_sha256": _hash(body)}
