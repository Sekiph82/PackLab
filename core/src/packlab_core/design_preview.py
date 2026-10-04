"""Bounded deterministic tessellation of Design Model operations for viewport previews."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .cross_section import CrossSection
from .design_model import DesignModelRevision
from .design_operations import DesignOperation, OperationKind
from .design_profile import DesignProfile
from .flexible_pack_authority import is_flexible_pack_model
from .geometry_adapter import TriangleMeshData
from .reconstruction import ScaleState

PREVIEW_CONTRACT = "packlab.design-preview.v1"
PREVIEW_AUTHORITY = "PREVIEW_PROXY"
MAX_REVOLVE_SEGMENTS = 512
MAX_PROFILE_SAMPLES = 2048
MAX_PREVIEW_VERTICES = 250_000
MAX_PREVIEW_TRIANGLES = 500_000
MAX_PREVIEW_OPERATIONS = 16
MAX_TOTAL_PREVIEW_VERTICES = 500_000
MAX_TOTAL_PREVIEW_TRIANGLES = 1_000_000


class DesignPreviewError(ValueError):
    """Raised when a preview request or its parametric source is invalid or unbounded."""


@dataclass(frozen=True, slots=True)
class DesignPreview:
    """Derived viewport mesh with explicit parent and feature provenance."""

    mesh: TriangleMeshData
    model_revision_id: str
    scan_master_revision_id: str | None
    scan_master_geometry_sha256: str | None
    parent_binding_revision_id: str | None
    scale_state: ScaleState
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    feature_vertex_indices: tuple[tuple[str, tuple[int, ...]], ...]
    authority_class: str = PREVIEW_AUTHORITY
    contract: str = PREVIEW_CONTRACT
    standalone_root_revision_id: str | None = None
    flexible_pack_design_only: bool = False

    def __post_init__(self) -> None:
        if self.authority_class != PREVIEW_AUTHORITY or self.contract != PREVIEW_CONTRACT:
            raise DesignPreviewError("preview_authority_invalid")
        if not isinstance(self.flexible_pack_design_only, bool):
            raise DesignPreviewError("preview_flexible_pack_flag_invalid")
        if (
            self.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
            or self.mold_use_authorized is not False
        ):
            raise DesignPreviewError("preview_physical_authority_invalid")
        captured = (
            self.scan_master_revision_id is not None
            and self.scan_master_geometry_sha256 is not None
            and self.parent_binding_revision_id is not None
            and self.standalone_root_revision_id is None
        )
        standalone = (
            self.standalone_root_revision_id is not None
            and self.scan_master_revision_id is None
            and self.scan_master_geometry_sha256 is None
            and self.parent_binding_revision_id is None
        )
        if not captured and not standalone:
            raise DesignPreviewError("preview_parent_authority_invalid")

    def as_dict(self) -> dict[str, object]:
        """Return metadata only; geometry remains a disposable derived payload."""
        if self.standalone_root_revision_id is not None:
            payload: dict[str, object] = {
                "contract": self.contract,
                "authority_class": self.authority_class,
                "model_revision_id": self.model_revision_id,
                "parent_authority": {
                    "kind": "STANDALONE_DESIGN_GEOMETRY",
                    "root_revision_id": self.standalone_root_revision_id,
                },
                "scale_state": self.scale_state.value,
                "coordinate_unit": self.coordinate_unit,
                "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
                "mold_use_authorized": self.mold_use_authorized,
                "vertex_count": len(self.mesh.vertices),
                "triangle_count": len(self.mesh.triangles),
                "feature_vertex_indices": [
                    {"feature_id": feature_id, "indices": list(indices)}
                    for feature_id, indices in self.feature_vertex_indices
                ],
                "disposable": True,
                "scan_master_promoted": False,
            }
        else:
            payload = {
                "contract": self.contract,
                "authority_class": self.authority_class,
                "model_revision_id": self.model_revision_id,
                "scan_master_revision_id": self.scan_master_revision_id,
                "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
                "parent_binding_revision_id": self.parent_binding_revision_id,
                "scale_state": self.scale_state.value,
                "coordinate_unit": self.coordinate_unit,
                "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
                "mold_use_authorized": self.mold_use_authorized,
                "vertex_count": len(self.mesh.vertices),
                "triangle_count": len(self.mesh.triangles),
                "feature_vertex_indices": [
                    {"feature_id": feature_id, "indices": list(indices)}
                    for feature_id, indices in self.feature_vertex_indices
                ],
                "disposable": True,
                "scan_master_promoted": False,
            }
        if self.flexible_pack_design_only:
            payload["authority_and_limitations"] = {
                "flexible_pack_design_only": True,
                "captured_geometry_authority": False,
                "scan_master_promotion_allowed": False,
                "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
                "mold_use_authorized": False,
                "manufacturing_authority": False,
                "certified_volume_claimed": False,
                "physical_tolerance_claimed": False,
                "measured_film_deformation_claimed": False,
            }
        return payload


def tessellate_design_preview(
    model: DesignModelRevision,
    *,
    profiles: tuple[DesignProfile, ...] = (),
    cross_sections: tuple[CrossSection, ...] = (),
    operations: tuple[DesignOperation, ...],
    chord_tolerance: float,
    profile_samples: int = 128,
    maximum_angular_segments: int = 256,
) -> tuple[DesignPreview, ...]:
    """Create deterministic PREVIEW_PROXY meshes under explicit work bounds.

    Loft inputs use their authored corresponding polygon vertices. Revolves use
    endpoint-inclusive profile samples and a full closed angular sweep.
    """
    _validate_request(model, profiles, cross_sections, operations)
    if (
        isinstance(chord_tolerance, bool)
        or not isinstance(chord_tolerance, (int, float))
        or not math.isfinite(chord_tolerance)
        or chord_tolerance <= 0
    ):
        raise DesignPreviewError("chord_tolerance_must_be_finite_and_positive")
    _bounded_integer(profile_samples, 2, MAX_PROFILE_SAMPLES, "profile_sample_count_invalid")
    _bounded_integer(
        maximum_angular_segments,
        8,
        MAX_REVOLVE_SEGMENTS,
        "maximum_angular_segments_invalid",
    )
    if not isinstance(operations, tuple) or not operations:
        raise DesignPreviewError("preview_operations_required")

    profile_by_id = {profile.profile_id: profile for profile in profiles}
    section_by_id = {section.section_id: section for section in cross_sections}
    if len(operations) > MAX_PREVIEW_OPERATIONS:
        raise DesignPreviewError("preview_operation_count_exceeded")
    results_list: list[DesignPreview] = []
    total_vertices = 0
    total_triangles = 0
    for operation in sorted(operations, key=lambda item: item.operation_id):
        result = _tessellate_operation(
            model,
            operation,
            profile_by_id,
            section_by_id,
            float(chord_tolerance),
            profile_samples,
            maximum_angular_segments,
        )
        total_vertices += len(result.mesh.vertices)
        total_triangles += len(result.mesh.triangles)
        if (
            total_vertices > MAX_TOTAL_PREVIEW_VERTICES
            or total_triangles > MAX_TOTAL_PREVIEW_TRIANGLES
        ):
            raise DesignPreviewError("preview_total_work_bound_exceeded")
        results_list.append(result)
    return tuple(results_list)


def _tessellate_operation(
    model: DesignModelRevision,
    operation: DesignOperation,
    profiles: dict[str, DesignProfile],
    sections: dict[str, CrossSection],
    chord_tolerance: float,
    profile_samples: int,
    maximum_angular_segments: int,
) -> DesignPreview:
    if (
        operation.model_revision_id != model.revision_id
        or operation.scale_state is not model.scale_state
        or operation.coordinate_unit != model.coordinate_unit
        or operation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or operation.mold_use_authorized is not False
        or any(
            feature_id not in {feature.feature_id for feature in model.features}
            for feature_id in operation.parent_feature_ids
        )
    ):
        raise DesignPreviewError("operation_model_or_authority_stale")
    if operation.kind is OperationKind.REVOLVE:
        mesh, mapping = _tessellate_revolve(
            operation,
            profiles,
            chord_tolerance,
            profile_samples,
            maximum_angular_segments,
        )
    elif operation.kind is OperationKind.LOFT:
        mesh, mapping = _tessellate_loft(model, operation, sections)
    else:
        raise DesignPreviewError("operation_kind_unsupported")
    _check_work_bounds(len(mesh.vertices), len(mesh.triangles))
    return DesignPreview(
        mesh=mesh,
        model_revision_id=model.revision_id,
        scan_master_revision_id=model.fitted_to_scan_master_revision_id,
        scan_master_geometry_sha256=model.scan_master_geometry_sha256,
        parent_binding_revision_id=model.parent_binding_revision_id,
        scale_state=model.scale_state,
        coordinate_unit=model.coordinate_unit,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        feature_vertex_indices=mapping,
        standalone_root_revision_id=(
            model.standalone_root.revision_id if model.standalone_root is not None else None
        ),
        flexible_pack_design_only=is_flexible_pack_model(model),
    )


def _tessellate_revolve(
    operation: DesignOperation,
    profiles: dict[str, DesignProfile],
    chord_tolerance: float,
    profile_samples: int,
    maximum_angular_segments: int,
) -> tuple[TriangleMeshData, tuple[tuple[str, tuple[int, ...]], ...]]:
    if (
        len(operation.input_ids) != 1
        or operation.input_ids[0] not in profiles
        or operation.axis_origin is None
        or operation.axis_direction is None
        or operation.angle_degrees is None
    ):
        raise DesignPreviewError("revolve_preview_inputs_unsupported_or_stale")
    profile = profiles[operation.input_ids[0]]
    samples = profile.sample(profile_samples)
    max_radius = max(sample.radius for sample in samples)
    segments = _segments_for_tolerance(
        max_radius, chord_tolerance, maximum_angular_segments, operation.angle_degrees
    )
    full_sweep = operation.angle_degrees == 360.0
    angular_vertices = segments if full_sweep else segments + 1
    _check_work_bounds(len(samples) * angular_vertices, 2 * (len(samples) - 1) * segments)
    axis = operation.axis_direction
    reference = (1.0, 0.0, 0.0) if abs(axis[0]) < 0.9 else (0.0, 1.0, 0.0)
    basis_u = _normalize(_cross(axis, reference))
    basis_v = _normalize(_cross(axis, basis_u))
    vertices: list[tuple[float, float, float]] = []
    rings: list[tuple[int, ...]] = []
    for sample in samples:
        ring_indices: list[int] = []
        for step in range(angular_vertices):
            theta = math.radians(operation.angle_degrees) * step / segments
            cos_theta, sin_theta = math.cos(theta), math.sin(theta)
            radial = tuple(
                cos_theta * basis_u[index] + sin_theta * basis_v[index] for index in range(3)
            )
            point = (
                operation.axis_origin[0] + sample.axial * axis[0] + sample.radius * radial[0],
                operation.axis_origin[1] + sample.axial * axis[1] + sample.radius * radial[1],
                operation.axis_origin[2] + sample.axial * axis[2] + sample.radius * radial[2],
            )
            ring_indices.append(len(vertices))
            vertices.append(point)
        rings.append(tuple(ring_indices))
    triangles = _connect_rings(rings, closed=operation.angle_degrees == 360.0)
    mesh = TriangleMeshData(tuple(vertices), triangles)
    mapping = ((operation.parent_feature_ids[0], tuple(range(len(vertices)))),)
    return mesh, mapping


def _tessellate_loft(
    model: DesignModelRevision,
    operation: DesignOperation,
    sections: dict[str, CrossSection],
) -> tuple[TriangleMeshData, tuple[tuple[str, tuple[int, ...]], ...]]:
    if (
        len(operation.input_ids) < 2
        or len(operation.input_ids) != len(operation.section_positions)
        or any(section_id not in sections for section_id in operation.input_ids)
        or len(operation.parent_feature_ids) < len(operation.input_ids)
    ):
        raise DesignPreviewError("loft_preview_inputs_unsupported_or_stale")
    ordered_sections = tuple(sections[section_id] for section_id in operation.input_ids)
    point_count = len(ordered_sections[0].points)
    if any(len(section.points) != point_count for section in ordered_sections):
        raise DesignPreviewError("loft_preview_topology_mismatch")
    _check_work_bounds(
        len(ordered_sections) * point_count,
        2 * (len(ordered_sections) - 1) * point_count,
    )
    vertices: list[tuple[float, float, float]] = []
    rings: list[tuple[int, ...]] = []
    mappings: list[tuple[str, tuple[int, ...]]] = []
    feature_by_id = {feature.feature_id: feature for feature in model.features}
    for feature_id, section, axial in zip(
        operation.parent_feature_ids[: len(ordered_sections)],
        ordered_sections,
        operation.section_positions,
        strict=True,
    ):
        if (
            feature_id not in feature_by_id
            or feature_by_id[feature_id].component_id != section.component_id
        ):
            raise DesignPreviewError("loft_feature_component_mismatch")
        ring: list[int] = []
        for point in section.points:
            ring.append(len(vertices))
            vertices.append((point.x, point.y, axial))
        rings.append(tuple(ring))
        mappings.append((feature_id, tuple(ring)))
    triangles = _connect_rings(rings, closed=True)
    return TriangleMeshData(tuple(vertices), triangles), tuple(mappings)


def _connect_rings(
    rings: list[tuple[int, ...]], *, closed: bool
) -> tuple[tuple[int, int, int], ...]:
    triangles: list[tuple[int, int, int]] = []
    for lower, upper in zip(rings, rings[1:]):
        count = len(lower)
        if count != len(upper):
            raise DesignPreviewError("preview_ring_topology_mismatch")
        for index in range(count if closed else count - 1):
            following = (index + 1) % count
            a, b, c, d = lower[index], lower[following], upper[following], upper[index]
            triangles.extend(((a, b, c), (a, c, d)))
    return tuple(triangles)


def _segments_for_tolerance(
    radius: float, tolerance: float, maximum: int, angle_degrees: float
) -> int:
    if radius <= tolerance:
        return min(8, maximum)
    cosine = 1.0 - tolerance / radius
    if cosine <= -1.0:
        required = 8
    elif cosine >= 1.0:
        raise DesignPreviewError("chord_tolerance_exceeds_work_bound")
    else:
        required = max(
            1,
            math.ceil(math.radians(angle_degrees) / (2.0 * math.acos(cosine))),
        )
        required = max(8, required)
    if required > maximum:
        raise DesignPreviewError("chord_tolerance_exceeds_work_bound")
    return required


def _validate_request(
    model: DesignModelRevision,
    profiles: tuple[DesignProfile, ...],
    cross_sections: tuple[CrossSection, ...],
    operations: tuple[DesignOperation, ...],
) -> None:
    if not isinstance(model, DesignModelRevision):
        raise DesignPreviewError("design_model_revision_required")
    if (
        model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
        or model.scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}
    ):
        raise DesignPreviewError("design_model_preview_authority_invalid")
    if not isinstance(profiles, tuple) or any(
        not isinstance(item, DesignProfile) for item in profiles
    ):
        raise DesignPreviewError("profiles_must_be_immutable_tuple")
    if not isinstance(cross_sections, tuple) or any(
        not isinstance(item, CrossSection) for item in cross_sections
    ):
        raise DesignPreviewError("cross_sections_must_be_immutable_tuple")
    if not isinstance(operations, tuple) or any(
        not isinstance(item, DesignOperation) for item in operations
    ):
        raise DesignPreviewError("operations_must_be_immutable_tuple")
    if len({item.profile_id for item in profiles}) != len(profiles):
        raise DesignPreviewError("profile_id_duplicate")
    if len({item.section_id for item in cross_sections}) != len(cross_sections):
        raise DesignPreviewError("section_id_duplicate")
    if len({item.operation_id for item in operations}) != len(operations):
        raise DesignPreviewError("operation_id_duplicate")
    expected_unit = (
        "reconstruction_units" if model.scale_state is ScaleState.RELATIVE else "mm_unverified"
    )
    if model.coordinate_unit != expected_unit:
        raise DesignPreviewError("design_model_unit_invalid")
    if any(
        item.scale_state is not model.scale_state or item.coordinate_unit != model.coordinate_unit
        for item in profiles
    ) or any(
        item.scale_state is not model.scale_state or item.coordinate_unit != model.coordinate_unit
        for item in cross_sections
    ):
        raise DesignPreviewError("preview_input_unit_mismatch")


def _bounded_integer(value: int, minimum: int, maximum: int, error: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not minimum <= value <= maximum:
        raise DesignPreviewError(error)


def _check_work_bounds(vertices: int, triangles: int) -> None:
    if vertices > MAX_PREVIEW_VERTICES or triangles > MAX_PREVIEW_TRIANGLES:
        raise DesignPreviewError("preview_work_bound_exceeded")


def _cross(left: tuple[float, ...], right: tuple[float, ...]) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _normalize(vector: tuple[float, ...]) -> tuple[float, float, float]:
    length = math.sqrt(sum(value * value for value in vector))
    if not math.isfinite(length) or length <= 0:
        raise DesignPreviewError("revolve_axis_basis_invalid")
    return (vector[0] / length, vector[1] / length, vector[2] / length)


__all__ = [
    "MAX_PREVIEW_TRIANGLES",
    "MAX_PREVIEW_VERTICES",
    "MAX_PREVIEW_OPERATIONS",
    "MAX_PROFILE_SAMPLES",
    "MAX_REVOLVE_SEGMENTS",
    "MAX_TOTAL_PREVIEW_TRIANGLES",
    "MAX_TOTAL_PREVIEW_VERTICES",
    "PREVIEW_AUTHORITY",
    "PREVIEW_CONTRACT",
    "DesignPreview",
    "DesignPreviewError",
    "tessellate_design_preview",
]
