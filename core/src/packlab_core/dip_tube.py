"""Backend-neutral parametric dip-tube paths and immutable Design Model revisions."""

from __future__ import annotations

import math
from dataclasses import dataclass

from .design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    resolve_design_model_feature,
    revise_design_model_revision,
    stable_feature_id,
)
from .design_model_binding import DesignModelParentBindingRevision
from .reconstruction import ScaleState

_MAX_SEGMENTS = 32
_JOIN_TOLERANCE = 1e-8
_LENGTH_RELATIVE_TOLERANCE = 1e-3
_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class DipTubeError(ValueError):
    """Raised when a parametric dip-tube path or exact attachment is invalid."""


@dataclass(frozen=True, slots=True)
class CubicBezierSegment:
    """One cubic centerline span, stored as four immutable 3D control points."""

    control_points: tuple[tuple[float, float, float], ...]

    def __post_init__(self) -> None:
        if not isinstance(self.control_points, tuple) or len(self.control_points) != 4:
            raise DipTubeError("dip_tube_bezier_requires_four_control_points")
        for point in self.control_points:
            _point(point, "dip_tube_control_point")
        if _distance(self.control_points[0], self.control_points[3]) <= _JOIN_TOLERANCE:
            raise DipTubeError("dip_tube_segment_degenerate")
        if _distance(self.control_points[0], self.control_points[1]) <= _JOIN_TOLERANCE:
            raise DipTubeError("dip_tube_start_tangent_degenerate")
        if _distance(self.control_points[2], self.control_points[3]) <= _JOIN_TOLERANCE:
            raise DipTubeError("dip_tube_end_tangent_degenerate")

    @classmethod
    def straight(
        cls, start: tuple[float, float, float], end: tuple[float, float, float]
    ) -> CubicBezierSegment:
        """Represent a straight span as a cubic with collinear, evenly spaced handles."""
        first = _point(start, "dip_tube_start")
        last = _point(end, "dip_tube_end")
        return cls(
            (
                first,
                _point(
                    tuple(first[i] + (last[i] - first[i]) / 3.0 for i in range(3)),
                    "dip_tube_control_point",
                ),
                _point(
                    tuple(first[i] + 2.0 * (last[i] - first[i]) / 3.0 for i in range(3)),
                    "dip_tube_control_point",
                ),
                last,
            )
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "kind": "cubic_bezier",
            "control_points": [list(point) for point in self.control_points],
        }


@dataclass(frozen=True, slots=True)
class DipTubePath:
    """Bounded G1-connected sequence of cubic Bezier centerline spans."""

    segments: tuple[CubicBezierSegment, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.segments, tuple)
            or not self.segments
            or len(self.segments) > _MAX_SEGMENTS
            or any(not isinstance(item, CubicBezierSegment) for item in self.segments)
        ):
            raise DipTubeError("dip_tube_path_segment_count_invalid")
        for previous, following in zip(self.segments, self.segments[1:]):
            end = previous.control_points[3]
            start = following.control_points[0]
            if _distance(end, start) > _JOIN_TOLERANCE:
                raise DipTubeError("dip_tube_path_discontinuous")
            incoming = _point(
                tuple(end[i] - previous.control_points[2][i] for i in range(3)),
                "dip_tube_join_tangent",
            )
            outgoing = _point(
                tuple(following.control_points[1][i] - start[i] for i in range(3)),
                "dip_tube_join_tangent",
            )
            incoming_unit = _normalize(incoming)
            outgoing_unit = _normalize(outgoing)
            if _distance(incoming_unit, outgoing_unit) > _JOIN_TOLERANCE:
                raise DipTubeError("dip_tube_path_not_piecewise_smooth")

    @classmethod
    def straight(
        cls, start: tuple[float, float, float], end: tuple[float, float, float]
    ) -> DipTubePath:
        return cls((CubicBezierSegment.straight(start, end),))

    def length(self) -> float:
        """Return a fixed-resolution composite Simpson estimate in path coordinate units."""
        return math.fsum(_bezier_length(segment) for segment in self.segments)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.dip-tube-path.v1",
            "representation": "piecewise_cubic_bezier_centerline",
            "segments": [segment.as_dict() for segment in self.segments],
            "segment_limit": _MAX_SEGMENTS,
        }


@dataclass(frozen=True, slots=True)
class DipTubeAttachmentReference:
    """Exact pump model feature pin used as the dip tube's design attachment."""

    trigger_pump_model_revision_id: str
    trigger_pump_feature_id: str

    def __post_init__(self) -> None:
        if (
            not isinstance(self.trigger_pump_model_revision_id, str)
            or not self.trigger_pump_model_revision_id.startswith("design-model:")
            or not isinstance(self.trigger_pump_feature_id, str)
            or not self.trigger_pump_feature_id.startswith("packlab-feature:")
        ):
            raise DipTubeError("dip_tube_attachment_reference_invalid")

    def as_dict(self) -> dict[str, str]:
        return {
            "role": "trigger_pump_outlet",
            "model_revision_id": self.trigger_pump_model_revision_id,
            "feature_id": self.trigger_pump_feature_id,
        }


@dataclass(frozen=True, slots=True)
class DipTubeComponentRevision:
    """Dip-tube view over an immutable Design Model component revision."""

    model: DesignModelRevision
    feature_id: str
    path: DipTubePath
    length: float
    diameter: float
    attachment: DipTubeAttachmentReference

    def __post_init__(self) -> None:
        if not isinstance(self.model, DesignModelRevision):
            raise DipTubeError("dip_tube_design_model_revision_required")
        if not isinstance(self.attachment, DipTubeAttachmentReference):
            raise DipTubeError("dip_tube_attachment_reference_invalid")
        _validate_dimensions(self.path, self.length, self.diameter)
        try:
            feature = resolve_design_model_feature(self.model, self.feature_id)
        except DesignModelError as error:
            raise DipTubeError("dip_tube_feature_stale") from error
        if feature.feature_kind is not FeatureKind.DIP_TUBE:
            raise DipTubeError("dip_tube_feature_kind_invalid")
        parameters = {item.parameter_id: item.as_dict() for item in self.model.parameters}
        expected = {
            item.parameter_id: item.as_dict()
            for item in _parameters(
                self.path,
                self.length,
                self.diameter,
                self.attachment,
                self.model.coordinate_unit,
            )
        }
        if any(parameters.get(key) != value for key, value in expected.items()):
            raise DipTubeError("dip_tube_component_model_parameter_mismatch")

    @property
    def revision_id(self) -> str:
        return self.model.revision_id

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.dip-tube-component.v1",
            "revision_id": self.revision_id,
            "design_model_revision_id": self.model.revision_id,
            "feature_id": self.feature_id,
            "path": self.path.as_dict(),
            "length": self.length,
            "diameter": self.diameter,
            "coordinate_unit": self.model.coordinate_unit,
            "scale_state": self.model.scale_state.value,
            "attachment": self.attachment.as_dict(),
            "physical_accuracy_validation_status": self.model.physical_accuracy_validation_status,
            "mold_use_authorized": False,
            "geometry_generated": False,
            "collision_checked": False,
        }


def create_dip_tube_component(
    parent_binding: DesignModelParentBindingRevision,
    trigger_pump_model: DesignModelRevision,
    *,
    expected_trigger_pump_revision_id: str,
    trigger_pump_feature_id: str,
    component_id: str,
    semantic_key: str,
    path: DipTubePath,
    length: float,
    diameter: float,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DipTubeComponentRevision:
    """Create a Design Model component without reading or fitting Scan Master geometry."""
    _validate_attachment(
        parent_binding,
        trigger_pump_model,
        expected_trigger_pump_revision_id,
        trigger_pump_feature_id,
    )
    _validate_dimensions(path, length, diameter)
    feature = DesignModelFeatureReference(
        stable_feature_id(component_id, FeatureKind.DIP_TUBE, semantic_key),
        component_id,
        FeatureKind.DIP_TUBE,
        semantic_key,
    )
    attachment = DipTubeAttachmentReference(trigger_pump_model.revision_id, trigger_pump_feature_id)
    model = create_design_model_revision(
        parent_binding,
        package_family=PackageFamily.OTHER,
        parameters=_parameters(
            path,
            length,
            diameter,
            attachment,
            _coordinate_unit(parent_binding.scale_state),
        ),
        features=(feature,),
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    return DipTubeComponentRevision(model, feature.feature_id, path, length, diameter, attachment)


def edit_dip_tube_component(
    current: DipTubeComponentRevision,
    trigger_pump_model: DesignModelRevision,
    *,
    expected_current_revision_id: str,
    expected_trigger_pump_revision_id: str,
    trigger_pump_feature_id: str,
    path: DipTubePath,
    length: float,
    diameter: float,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DipTubeComponentRevision:
    """Create a new immutable parameter edit; it performs no collision or mesh operation."""
    if not isinstance(current, DipTubeComponentRevision):
        raise DipTubeError("dip_tube_component_revision_required")
    if current.revision_id != expected_current_revision_id:
        raise DipTubeError("dip_tube_component_revision_stale")
    _validate_attachment(
        current.model.parent_binding_revision_id,
        trigger_pump_model,
        expected_trigger_pump_revision_id,
        trigger_pump_feature_id,
        current_model=current.model,
    )
    _validate_dimensions(path, length, diameter)
    attachment = DipTubeAttachmentReference(trigger_pump_model.revision_id, trigger_pump_feature_id)
    feature = resolve_design_model_feature(current.model, current.feature_id)
    if feature.feature_kind is not FeatureKind.DIP_TUBE:
        raise DipTubeError("dip_tube_feature_kind_invalid")
    parameters = _parameters(path, length, diameter, attachment, current.model.coordinate_unit)
    preserved = tuple(
        parameter
        for parameter in current.model.parameters
        if parameter.parameter_id not in {item.parameter_id for item in parameters}
    )
    model = revise_design_model_revision(
        current.model,
        parameters=(*preserved, *parameters),
        features=current.model.features,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    return DipTubeComponentRevision(model, current.feature_id, path, length, diameter, attachment)


def _validate_attachment(
    parent_binding: object,
    pump: DesignModelRevision,
    expected_revision_id: str,
    feature_id: str,
    *,
    current_model: DesignModelRevision | None = None,
) -> None:
    if not isinstance(pump, DesignModelRevision):
        raise DipTubeError("trigger_pump_design_model_required")
    if pump.revision_id != expected_revision_id:
        raise DipTubeError("trigger_pump_model_revision_stale")
    try:
        feature = resolve_design_model_feature(pump, feature_id)
    except DesignModelError as error:
        raise DipTubeError("trigger_pump_attachment_feature_stale") from error
    if feature.feature_kind is not FeatureKind.TRIGGER_PUMP:
        raise DipTubeError("trigger_pump_attachment_feature_invalid")
    if current_model is None:
        if not isinstance(parent_binding, DesignModelParentBindingRevision):
            raise DipTubeError("dip_tube_parent_binding_required")
        same_parent = (
            parent_binding.project_id == pump.project_id
            and parent_binding.fitted_to_scan_master_revision_id
            == pump.fitted_to_scan_master_revision_id
            and parent_binding.scan_master_geometry_sha256 == pump.scan_master_geometry_sha256
            and parent_binding.scale_state is pump.scale_state
            and parent_binding.scale_provenance_id == pump.scale_provenance_id
            and _coordinate_unit(parent_binding.scale_state) == pump.coordinate_unit
        )
    else:
        same_parent = (
            current_model.project_id == pump.project_id
            and current_model.fitted_to_scan_master_revision_id
            == pump.fitted_to_scan_master_revision_id
            and current_model.scan_master_geometry_sha256 == pump.scan_master_geometry_sha256
            and current_model.scale_state is pump.scale_state
            and current_model.scale_provenance_id == pump.scale_provenance_id
            and current_model.coordinate_unit == pump.coordinate_unit
        )
    if not same_parent:
        raise DipTubeError("dip_tube_attachment_parent_or_scale_mismatch")
    if pump.physical_accuracy_validation_status != _DEFERRED or pump.mold_use_authorized:
        raise DipTubeError("trigger_pump_physical_authority_invalid")


def _validate_dimensions(path: DipTubePath, length: float, diameter: float) -> None:
    if not isinstance(path, DipTubePath):
        raise DipTubeError("dip_tube_path_required")
    for value, field in ((length, "length"), (diameter, "diameter")):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0.0
        ):
            raise DipTubeError(f"dip_tube_{field}_must_be_positive_finite")
    estimated = path.length()
    if abs(estimated - float(length)) > max(1e-6, float(length) * _LENGTH_RELATIVE_TOLERANCE):
        raise DipTubeError("dip_tube_length_path_mismatch")


def _coordinate_unit(scale_state: ScaleState) -> str:
    return "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"


def _parameters(
    path: DipTubePath,
    length: float,
    diameter: float,
    attachment: DipTubeAttachmentReference,
    unit: str,
) -> tuple[DesignModelParameter, ...]:
    return (
        DesignModelParameter("dip_tube.attachment", attachment.as_dict(), ParameterType.OBJECT),
        DesignModelParameter("dip_tube.diameter", float(diameter), ParameterType.NUMBER, unit),
        DesignModelParameter("dip_tube.length", float(length), ParameterType.NUMBER, unit),
        DesignModelParameter(
            "dip_tube.path", {**path.as_dict(), "coordinate_unit": unit}, ParameterType.OBJECT
        ),
    )


def _point(point: object, field: str) -> tuple[float, float, float]:
    if (
        not isinstance(point, tuple)
        or len(point) != 3
        or any(
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            for value in point
        )
    ):
        raise DipTubeError(f"{field}_invalid")
    return tuple(float(value) for value in point)  # type: ignore[return-value]


def _distance(first: tuple[float, float, float], second: tuple[float, float, float]) -> float:
    return math.sqrt(math.fsum((first[i] - second[i]) ** 2 for i in range(3)))


def _normalize(vector: tuple[float, float, float]) -> tuple[float, float, float]:
    magnitude = math.sqrt(math.fsum(value * value for value in vector))
    if magnitude <= _JOIN_TOLERANCE:
        raise DipTubeError("dip_tube_path_tangent_degenerate")
    return tuple(value / magnitude for value in vector)  # type: ignore[return-value]


def _bezier_length(segment: CubicBezierSegment) -> float:
    # Composite Simpson integration with a fixed even subdivision count is deterministic.
    subdivisions = 256
    step = 1.0 / subdivisions
    points = segment.control_points
    speeds = []
    for index in range(subdivisions + 1):
        t = index * step
        one_minus = 1.0 - t
        derivative = tuple(
            3.0 * one_minus * one_minus * (points[1][axis] - points[0][axis])
            + 6.0 * one_minus * t * (points[2][axis] - points[1][axis])
            + 3.0 * t * t * (points[3][axis] - points[2][axis])
            for axis in range(3)
        )
        speeds.append(math.sqrt(math.fsum(value * value for value in derivative)))
    weighted = math.fsum(
        (1 if index in {0, subdivisions} else 4 if index % 2 else 2) * speed
        for index, speed in enumerate(speeds)
    )
    return weighted * step / 3.0


__all__ = [
    "CubicBezierSegment",
    "DipTubeAttachmentReference",
    "DipTubeComponentRevision",
    "DipTubeError",
    "DipTubePath",
    "create_dip_tube_component",
    "edit_dip_tube_component",
]
