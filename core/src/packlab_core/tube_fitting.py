"""Source-explicit fitting of nominal tube dimensions into the tube family model."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from .bounding_dimensions import BoundingDimensions
from .cross_section_measurement import CrossSectionMeasurement
from .design_model_binding import (
    DesignModelParentBindingRevision,
    StandaloneDesignGeometryRoot,
    StandaloneDesignGeometrySourceKind,
    inspect_design_model_parent,
)
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision
from .tube_family import TubeFamilyDimensions, TubeFamilyRevision, build_tube_family
from .two_point_measurement import TwoPointDistanceMeasurement

_PREFIX = "tube-fit:"
_DEFERRED = "DEFERRED_OWNER_VALIDATION"
_DIMENSION_FIELDS = (
    "body_length",
    "body_diameter",
    "shoulder_length",
    "shoulder_diameter",
    "neck_length",
    "neck_diameter",
    "cap_height",
    "cap_diameter",
    "crimp_length",
    "crimp_thickness",
)
_ARTIFACT_VALUE_FIELDS = {
    BoundingDimensions: {"height", "width", "depth"},
    CrossSectionMeasurement: {"major_diameter", "minor_diameter"},
    TwoPointDistanceMeasurement: {"distance"},
}


class TubeFittingError(ValueError):
    """Raised when tube dimensions lack explicit, consistent source authority."""


class TubeFitAuthorityMode(StrEnum):
    CAPTURED_SCAN_MASTER = "CAPTURED_SCAN_MASTER"
    STANDALONE_DESIGN_GEOMETRY = "STANDALONE_DESIGN_GEOMETRY"


class TubeDimensionSourceKind(StrEnum):
    CAPTURED_MEASUREMENT = "CAPTURED_MEASUREMENT"
    REFERENCE_DIMENSION = "REFERENCE_DIMENSION"
    USER_AUTHORED_NOMINAL_DIMENSION = "USER_AUTHORED_NOMINAL_DIMENSION"


@dataclass(frozen=True, slots=True)
class TubeDimensionEvidence:
    """One explicit source for one modeled dimension; captured values retain their artifact."""

    parameter_id: str
    source_kind: TubeDimensionSourceKind
    source_id: str
    value: float
    coordinate_unit: str
    measurement: (
        BoundingDimensions | CrossSectionMeasurement | TwoPointDistanceMeasurement | None
    ) = None
    measurement_value_field: str | None = None
    captured_scan_master_revision_id: str | None = None

    def __post_init__(self) -> None:
        if self.parameter_id not in _DIMENSION_FIELDS:
            raise TubeFittingError("tube_fit_parameter_id_unsupported")
        if not isinstance(self.source_kind, TubeDimensionSourceKind):
            raise TubeFittingError("tube_fit_source_kind_invalid")
        _identifier(self.source_id, "tube_fit_source_id")
        if (
            isinstance(self.value, bool)
            or not isinstance(self.value, (int, float))
            or not math.isfinite(self.value)
            or self.value <= 0.0
        ):
            raise TubeFittingError("tube_fit_dimension_value_invalid")
        if self.coordinate_unit not in {"reconstruction_units", "mm_unverified"}:
            raise TubeFittingError("tube_fit_coordinate_unit_unauthorized")
        if self.source_kind is TubeDimensionSourceKind.CAPTURED_MEASUREMENT:
            if not isinstance(
                self.measurement,
                (BoundingDimensions, CrossSectionMeasurement, TwoPointDistanceMeasurement),
            ):
                raise TubeFittingError("tube_fit_captured_measurement_required")
            if self.measurement.measurement_id != self.source_id:
                raise TubeFittingError("tube_fit_measurement_id_mismatch")
            allowed_fields = _ARTIFACT_VALUE_FIELDS.get(type(self.measurement))
            if allowed_fields is None or self.measurement_value_field not in allowed_fields:
                raise TubeFittingError("tube_fit_measurement_value_field_unsupported")
            measured = _measurement_value(self.measurement, self.measurement_value_field)
            if measured != self.value:
                raise TubeFittingError("tube_fit_measurement_value_mismatch")
            _identifier(self.captured_scan_master_revision_id, "captured_scan_master_revision_id")
            if self.measurement.coordinate_unit != self.coordinate_unit:
                raise TubeFittingError("tube_fit_measurement_unit_mismatch")
        elif (
            self.measurement is not None
            or self.measurement_value_field is not None
            or self.captured_scan_master_revision_id is not None
        ):
            raise TubeFittingError("tube_fit_reference_contains_captured_evidence")

    @classmethod
    def from_captured_measurement(
        cls,
        parameter_id: str,
        measurement: BoundingDimensions | CrossSectionMeasurement | TwoPointDistanceMeasurement,
        *,
        value_field: str,
        captured_scan_master_revision_id: str,
    ) -> TubeDimensionEvidence:
        value = _measurement_value(measurement, value_field)
        return cls(
            parameter_id,
            TubeDimensionSourceKind.CAPTURED_MEASUREMENT,
            measurement.measurement_id,
            value,
            measurement.coordinate_unit,
            measurement,
            value_field,
            captured_scan_master_revision_id,
        )

    @classmethod
    def from_reference_dimension(
        cls,
        parameter_id: str,
        value: float,
        *,
        coordinate_unit: str,
        source_id: str,
        user_authored: bool = False,
    ) -> TubeDimensionEvidence:
        return cls(
            parameter_id,
            (
                TubeDimensionSourceKind.USER_AUTHORED_NOMINAL_DIMENSION
                if user_authored
                else TubeDimensionSourceKind.REFERENCE_DIMENSION
            ),
            source_id,
            value,
            coordinate_unit,
        )

    def as_dict(self) -> dict[str, object]:
        if self.measurement is None:
            return {
                "parameter_id": self.parameter_id,
                "source_kind": self.source_kind.value,
                "source_id": self.source_id,
                "value": self.value,
                "coordinate_unit": self.coordinate_unit,
            }
        return {
            "parameter_id": self.parameter_id,
            "source_kind": self.source_kind.value,
            "source_id": self.source_id,
            "value": self.value,
            "coordinate_unit": self.coordinate_unit,
            "measurement_artifact_type": type(self.measurement).__name__,
            "measurement_value_field": self.measurement_value_field,
            "source_geometry_id": self.measurement.source_geometry_id,
            "normalized_geometry_revision": self.measurement.normalized_geometry_revision,
            "scale_state": self.measurement.scale_state.value,
            "scale_provenance_id": self.measurement.scale_provenance_id,
            "captured_scan_master_revision_id": self.captured_scan_master_revision_id,
        }


@dataclass(frozen=True, slots=True)
class TubeFitRevision:
    revision_id: str
    authority_mode: TubeFitAuthorityMode
    family: TubeFamilyRevision
    captured_measurements: tuple[TubeDimensionEvidence, ...]
    reference_dimensions: tuple[TubeDimensionEvidence, ...]
    user_authored_dimensions: tuple[TubeDimensionEvidence, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.authority_mode, TubeFitAuthorityMode):
            raise TubeFittingError("tube_fit_authority_mode_invalid")
        if not isinstance(self.family, TubeFamilyRevision):
            raise TubeFittingError("tube_fit_family_revision_required")
        expected_parent_kind = (
            "CAPTURED_SCAN_MASTER"
            if self.authority_mode is TubeFitAuthorityMode.CAPTURED_SCAN_MASTER
            else "STANDALONE_DESIGN_GEOMETRY"
        )
        if self.family.model.parent_kind.value != expected_parent_kind:
            raise TubeFittingError("tube_fit_family_parent_authority_mismatch")
        evidence_sets = (
            (self.captured_measurements, TubeDimensionSourceKind.CAPTURED_MEASUREMENT),
            (self.reference_dimensions, TubeDimensionSourceKind.REFERENCE_DIMENSION),
            (
                self.user_authored_dimensions,
                TubeDimensionSourceKind.USER_AUTHORED_NOMINAL_DIMENSION,
            ),
        )
        flattened: list[TubeDimensionEvidence] = []
        for values, expected_kind in evidence_sets:
            if not isinstance(values, tuple) or any(
                not isinstance(item, TubeDimensionEvidence) or item.source_kind is not expected_kind
                for item in values
            ):
                raise TubeFittingError("tube_fit_source_evidence_invalid")
            flattened.extend(values)
        if len(flattened) != len(_DIMENSION_FIELDS) or {
            item.parameter_id for item in flattened
        } != set(_DIMENSION_FIELDS):
            raise TubeFittingError("tube_fit_dimension_evidence_incomplete")
        if (self.authority_mode is TubeFitAuthorityMode.CAPTURED_SCAN_MASTER) != bool(
            self.captured_measurements
        ):
            raise TubeFittingError("tube_fit_captured_evidence_authority_mismatch")
        parameters = {item.parameter_id: item.value for item in self.family.model.parameters}
        if any(
            item.coordinate_unit != self.family.model.coordinate_unit
            or parameters.get(f"tube_{item.parameter_id}") != item.value
            for item in flattened
        ):
            raise TubeFittingError("tube_fit_evidence_model_parameter_mismatch")
        if self.revision_id != _fit_revision_id(
            self.authority_mode,
            self.family,
            self.captured_measurements,
            self.reference_dimensions,
            self.user_authored_dimensions,
        ):
            raise TubeFittingError("tube_fit_revision_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        modeled = [
            {
                "parameter_id": item.parameter_id,
                "value": item.value,
                "unit": item.unit or self.family.model.coordinate_unit,
                "source_kind": "MODELED_PARAMETER",
            }
            for item in self.family.model.parameters
            if item.parameter_id.removeprefix("tube_") in _DIMENSION_FIELDS
        ]
        model = self.family.model
        if self.authority_mode is TubeFitAuthorityMode.CAPTURED_SCAN_MASTER:
            parent_authority: dict[str, object] = {
                "kind": self.authority_mode.value,
                "binding_revision_id": model.parent_binding_revision_id,
                "scan_master_revision_id": model.fitted_to_scan_master_revision_id,
                "scan_master_geometry_sha256": model.scan_master_geometry_sha256,
                "scale_provenance_id": model.scale_provenance_id,
            }
        else:
            assert model.standalone_root is not None
            parent_authority = {
                "kind": self.authority_mode.value,
                "root": model.standalone_root.as_dict(),
            }
        return {
            "contract": "packlab.tube-fit.v1",
            "revision_id": self.revision_id,
            "parent_authority_mode": self.authority_mode.value,
            "parent_authority": parent_authority,
            "design_model_revision_id": model.revision_id,
            "scale_state": model.scale_state.value,
            "coordinate_unit": model.coordinate_unit,
            "captured_measurements": [item.as_dict() for item in self.captured_measurements],
            "reference_dimensions": [item.as_dict() for item in self.reference_dimensions],
            "user_authored_dimensions": [item.as_dict() for item in self.user_authored_dimensions],
            "modeled_parameters": modeled,
            "flexible_wall_deformation_inferred": False,
            "wall_thickness_inferred": False,
            "material_inferred": False,
            "physical_accuracy_validation_status": _DEFERRED,
            "mold_use_authorized": False,
            "manufacturing_dimensions_claimed": False,
            "scan_master_mutated": False,
        }


def fit_tube_family(
    parent: DesignModelParentBindingRevision | StandaloneDesignGeometryRoot,
    dimensions: TubeFamilyDimensions,
    evidence: tuple[TubeDimensionEvidence, ...],
    *,
    authority_mode: TubeFitAuthorityMode,
    component_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
    scan_master: ScanMasterRevision | None = None,
) -> TubeFitRevision:
    """Create a nominal tube model with selected and typed dimension-source authority."""
    if not isinstance(authority_mode, TubeFitAuthorityMode):
        raise TubeFittingError("tube_fit_authority_mode_required")
    if not isinstance(dimensions, TubeFamilyDimensions):
        raise TubeFittingError("tube_fit_dimensions_required")
    if not isinstance(evidence, tuple) or any(
        not isinstance(item, TubeDimensionEvidence) for item in evidence
    ):
        raise TubeFittingError("tube_fit_evidence_must_be_immutable_tuple")
    if len(evidence) != len(_DIMENSION_FIELDS):
        raise TubeFittingError("tube_fit_dimension_evidence_incomplete")
    if len({item.parameter_id for item in evidence}) != len(evidence):
        raise TubeFittingError("tube_fit_dimension_evidence_duplicate")
    by_parameter = {item.parameter_id: item for item in evidence}
    expected_values = dimensions.as_dict(
        "reconstruction_units"
        if getattr(parent, "scale_state", None) is ScaleState.RELATIVE
        else "mm_unverified"
    )
    for parameter_id in _DIMENSION_FIELDS:
        source = by_parameter.get(parameter_id)
        if source is None or source.value != expected_values[parameter_id]:
            raise TubeFittingError("tube_fit_dimension_evidence_contradictory")

    if authority_mode is TubeFitAuthorityMode.CAPTURED_SCAN_MASTER:
        if not isinstance(parent, DesignModelParentBindingRevision):
            raise TubeFittingError("captured_tube_fit_parent_binding_required")
        if not isinstance(scan_master, ScanMasterRevision):
            raise TubeFittingError("captured_tube_fit_scan_master_required")
        status = inspect_design_model_parent(
            parent,
            available_scan_masters=(scan_master,),
            latest_scan_master_revision_id=scan_master.revision_id,
            latest_reconstruction_revision_id=parent.reconstruction_revision_id,
        )
        if not status.pinned_parent_available or status.newer_scan_master_available:
            raise TubeFittingError("captured_tube_fit_parent_stale")
        if any(
            item.source_kind is TubeDimensionSourceKind.CAPTURED_MEASUREMENT
            and item.captured_scan_master_revision_id != scan_master.revision_id
            for item in evidence
        ):
            raise TubeFittingError("tube_fit_measurement_scan_master_mismatch")
        captured = tuple(
            item
            for item in evidence
            if item.source_kind is TubeDimensionSourceKind.CAPTURED_MEASUREMENT
        )
        if not captured:
            raise TubeFittingError("captured_tube_fit_measurement_required")
        if any(
            item.measurement is None
            or item.measurement.scale_state is not parent.scale_state
            or item.coordinate_unit != _coordinate_unit(parent.scale_state)
            or (
                parent.scale_state is ScaleState.RELATIVE
                and item.measurement.scale_provenance_id is not None
            )
            or (
                parent.scale_state is ScaleState.METRIC_UNVERIFIED
                and item.measurement.scale_provenance_id != parent.scale_provenance_id
            )
            for item in captured
        ):
            raise TubeFittingError("tube_fit_measurement_scale_parent_mismatch")
        manifest = scan_master.manifest
        parent_object_geometry_id = manifest.get("parent_object_geometry_revision_id")
        alignment = manifest.get("alignment_transform")
        transform = alignment.get("transform") if isinstance(alignment, Mapping) else None
        normalized_revision = (
            transform.get("transform_id") if isinstance(transform, Mapping) else None
        )
        if not isinstance(parent_object_geometry_id, str) or not isinstance(
            normalized_revision, str
        ):
            raise TubeFittingError("captured_tube_fit_normalized_parent_missing")
        if any(
            item.measurement is None
            or item.measurement.source_geometry_id != parent_object_geometry_id
            or item.measurement.normalized_geometry_revision != normalized_revision
            for item in captured
        ):
            raise TubeFittingError("tube_fit_measurement_geometry_parent_mismatch")
    else:
        if not isinstance(parent, StandaloneDesignGeometryRoot):
            raise TubeFittingError("standalone_tube_fit_root_required")
        if scan_master is not None:
            raise TubeFittingError("standalone_tube_fit_rejects_scan_master_parent")
        if any(
            item.source_kind is TubeDimensionSourceKind.CAPTURED_MEASUREMENT for item in evidence
        ):
            raise TubeFittingError("standalone_tube_fit_cannot_claim_captured_measurements")
        source_kinds = {item.source_kind for item in evidence}
        if (
            (
                parent.source_kind
                is StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS
                and source_kinds != {TubeDimensionSourceKind.USER_AUTHORED_NOMINAL_DIMENSION}
            )
            or (
                parent.source_kind is StandaloneDesignGeometrySourceKind.REFERENCE_DIMENSIONS
                and source_kinds != {TubeDimensionSourceKind.REFERENCE_DIMENSION}
            )
            or (
                parent.source_kind is StandaloneDesignGeometrySourceKind.REVIEWED_REUSABLE_TEMPLATE
                and source_kinds != {TubeDimensionSourceKind.REFERENCE_DIMENSION}
            )
        ):
            raise TubeFittingError("standalone_tube_fit_source_kind_mismatch")

    selected_unit = _coordinate_unit(parent.scale_state)
    if any(item.coordinate_unit != selected_unit for item in evidence):
        raise TubeFittingError("tube_fit_dimension_unit_mismatch")
    family = build_tube_family(
        parent,
        dimensions,
        component_id=component_id,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )
    captured = tuple(
        sorted(
            (
                item
                for item in evidence
                if item.source_kind is TubeDimensionSourceKind.CAPTURED_MEASUREMENT
            ),
            key=lambda item: item.parameter_id,
        )
    )
    references = tuple(
        sorted(
            (
                item
                for item in evidence
                if item.source_kind is TubeDimensionSourceKind.REFERENCE_DIMENSION
            ),
            key=lambda item: item.parameter_id,
        )
    )
    authored = tuple(
        sorted(
            (
                item
                for item in evidence
                if item.source_kind is TubeDimensionSourceKind.USER_AUTHORED_NOMINAL_DIMENSION
            ),
            key=lambda item: item.parameter_id,
        )
    )
    return TubeFitRevision(
        _fit_revision_id(authority_mode, family, captured, references, authored),
        authority_mode,
        family,
        captured,
        references,
        authored,
    )


def _fit_revision_id(
    authority_mode: TubeFitAuthorityMode,
    family: TubeFamilyRevision,
    captured: tuple[TubeDimensionEvidence, ...],
    references: tuple[TubeDimensionEvidence, ...],
    authored: tuple[TubeDimensionEvidence, ...],
) -> str:
    identity = {
        "contract": "packlab.tube-fit.v1",
        "authority_mode": authority_mode.value,
        "design_model_revision_id": family.model.revision_id,
        "captured_measurements": [item.as_dict() for item in captured],
        "reference_dimensions": [item.as_dict() for item in references],
        "user_authored_dimensions": [item.as_dict() for item in authored],
        "flexible_wall_deformation_inferred": False,
        "wall_thickness_inferred": False,
        "material_inferred": False,
        "physical_accuracy_validation_status": _DEFERRED,
        "mold_use_authorized": False,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return _PREFIX + digest


def _measurement_value(
    artifact: BoundingDimensions | CrossSectionMeasurement | TwoPointDistanceMeasurement,
    field: str,
) -> float:
    if isinstance(artifact, BoundingDimensions):
        values = {"height": artifact.height, "width": artifact.width, "depth": artifact.depth}
    elif isinstance(artifact, CrossSectionMeasurement):
        values = {
            "major_diameter": artifact.major_diameter,
            "minor_diameter": artifact.minor_diameter,
        }
    else:
        values = {"distance": artifact.distance}
    value = values.get(field)
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise TubeFittingError("tube_fit_measurement_field_invalid")
    return float(value)


def _coordinate_unit(scale_state: ScaleState) -> str:
    return "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"


def _identifier(value: object, field: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or len(value) > 128
        or not value[0].isalnum()
        or not all(character.isalnum() or character in "_.:+-" for character in value)
    ):
        raise TubeFittingError(f"{field}_invalid")
    return value


__all__ = [
    "TubeDimensionEvidence",
    "TubeDimensionSourceKind",
    "TubeFitAuthorityMode",
    "TubeFitRevision",
    "TubeFittingError",
    "fit_tube_family",
]
