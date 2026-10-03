"""Deterministic privacy-conscious export for PackLab measurement artifacts."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .bounding_dimensions import BoundingDimensions
from .capacity_estimation import CapacityEstimate
from .cross_section_measurement import CrossSectionMeasurement
from .design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    DesignModelRevision,
    FeatureKind,
    ParameterType,
)
from .horizontal_section import HorizontalSection
from .measurement_uncertainty import MeasurementUncertaintyReport
from .neck_finish_candidates import NeckFinishCandidateSet
from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256
from .two_point_measurement import TwoPointDistanceMeasurement
from .vertical_profile import VerticalProfile

MEASUREMENT_REPORT_VERSION = "packlab_measurement_report_v1"
_SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:+-]{0,127}$")
MeasurementArtifact = (
    BoundingDimensions
    | CapacityEstimate
    | CrossSectionMeasurement
    | HorizontalSection
    | MeasurementUncertaintyReport
    | NeckFinishCandidateSet
    | TwoPointDistanceMeasurement
    | VerticalProfile
)


class MeasurementReportError(ValueError):
    """Raised when report context or artifact parents are invalid or mixed."""


@dataclass(frozen=True, slots=True)
class MeasurementReportContext:
    project_id: str
    project_revision: str
    source_revision_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    coordinate_unit: str

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "project_revision",
            "source_revision_id",
            "source_geometry_id",
            "normalized_geometry_revision",
            "coordinate_unit",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not _SAFE_ID.fullmatch(value):
                raise MeasurementReportError(f"report_context_{name}_invalid")
        if not isinstance(self.scale_state, ScaleState):
            raise MeasurementReportError("report_context_scale_state_invalid")
        if self.scale_state is ScaleState.RELATIVE:
            if (
                self.scale_provenance_id is not None
                or self.coordinate_unit != "reconstruction_units"
            ):
                raise MeasurementReportError("report_context_relative_scale_mismatch")
        else:
            if (
                not isinstance(self.scale_provenance_id, str)
                or not _SAFE_ID.fullmatch(self.scale_provenance_id)
                or self.coordinate_unit
                != ("mm_unverified" if self.scale_state is ScaleState.METRIC_UNVERIFIED else "mm")
            ):
                raise MeasurementReportError("report_context_metric_scale_mismatch")


@dataclass(frozen=True, slots=True)
class MeasurementReport:
    context: MeasurementReportContext
    artifacts: tuple[dict[str, object], ...]
    report_version: str = MEASUREMENT_REPORT_VERSION
    modeled_closure_dimensions: tuple[dict[str, object], ...] = ()

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.measurement-report.v1",
            "report_version": self.report_version,
            "project": {
                "project_id": self.context.project_id,
                "project_revision": self.context.project_revision,
            },
            "source": {
                "source_revision_id": self.context.source_revision_id,
                "source_geometry_id": self.context.source_geometry_id,
                "normalized_geometry_revision": self.context.normalized_geometry_revision,
                "scale_provenance_id": self.context.scale_provenance_id,
                "scale_state": self.context.scale_state.value,
                "coordinate_unit": self.context.coordinate_unit,
            },
            "artifacts": [dict(item) for item in self.artifacts],
            "modeled_closure_dimensions": [dict(item) for item in self.modeled_closure_dimensions],
            "authority_and_limitations": {
                "authority_class": "OBJECT_CAPTURE_GEOMETRY_OR_EXPLICIT_INTERIOR_ASSUMPTION",
                "ai_visual_reference_authoritative": False,
                "certified_measurement_claimed": False,
                "mold_ready_claimed": False,
                "physical_accuracy_claimed": False,
                "modeled_closure_dimensions_are_captured_measurements": False,
                "modeled_closure_dimensions_certified": False,
                "private_raw_bytes_included": False,
                "ambient_identity_included": False,
            },
        }


def build_measurement_report(
    context: MeasurementReportContext,
    artifacts: tuple[MeasurementArtifact, ...],
    *,
    scan_master: ScanMasterRevision | None = None,
    design_model: DesignModelRevision | None = None,
    expected_scan_master_revision_id: str | None = None,
    expected_design_model_revision_id: str | None = None,
) -> MeasurementReport:
    """Build a deterministic report from captured measurements and optional modeled closure dimensions."""

    if not isinstance(artifacts, tuple):
        raise MeasurementReportError("report_artifacts_must_be_immutable_tuple")
    summaries = tuple(_summarize_artifact(context, artifact) for artifact in artifacts)
    ids = tuple(str(item["artifact_id"]) for item in summaries)
    if len(set(ids)) != len(ids):
        raise MeasurementReportError("report_duplicate_artifact_id")
    ordered = tuple(
        sorted(summaries, key=lambda item: (str(item["artifact_type"]), str(item["artifact_id"])))
    )
    closure_dimensions = _summarize_modeled_closure_dimensions(
        context,
        scan_master,
        design_model,
        expected_scan_master_revision_id=expected_scan_master_revision_id,
        expected_design_model_revision_id=expected_design_model_revision_id,
    )
    if not ordered and not closure_dimensions:
        raise MeasurementReportError("report_requires_captured_or_modeled_dimensions")
    return MeasurementReport(context, ordered, modeled_closure_dimensions=closure_dimensions)


def serialize_measurement_report(report: MeasurementReport) -> bytes:
    return json.dumps(
        report.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def render_measurement_report_markdown(report: MeasurementReport) -> str:
    """Render a compact human-readable view with the same stable artifact ordering."""

    context = report.context
    lines = [
        "# PackLab Measurement Report",
        "",
        f"- Project: `{context.project_id}` ({context.project_revision})",
        f"- Source revision: `{context.source_revision_id}`",
        f"- Geometry: `{context.source_geometry_id}` / normalized `{context.normalized_geometry_revision}`",
        f"- Scale: `{context.scale_state.value}` ({context.coordinate_unit}); provenance `{context.scale_provenance_id or 'none'}`",
        "",
        "## Measurement artifacts",
        "",
    ]
    for artifact in report.artifacts:
        summary = json.dumps(
            artifact["summary"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        uncertainty = json.dumps(
            artifact["uncertainty"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
        )
        lines.append(
            f"- **{artifact['artifact_type']}** `{artifact['artifact_id']}` ({artifact['units']}) — {summary}; uncertainty: {uncertainty}"
        )
    if report.modeled_closure_dimensions:
        lines.extend(["", "## Parametric closure dimensions", ""])
        for item in report.modeled_closure_dimensions:
            dimensions = json.dumps(
                item["dimensions"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
            fit_support = json.dumps(
                item["captured_fit_support"],
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
            )
            uncertainty = json.dumps(
                item["uncertainty"], sort_keys=True, separators=(",", ":"), ensure_ascii=True
            )
            lines.append(
                f"- **{item['closure_kind']}** `{item['feature_id']}` from Design Model `{item['design_model_revision_id']}` ({item['coordinate_unit']}) — dimensions: {dimensions}; captured fit support: {fit_support}; uncertainty: {uncertainty}; certified: no; mold-ready: no."
            )
    lines.extend(
        [
            "",
            "## Authority and limits",
            "",
            "Captured geometry and explicit interior assumptions retain separate authority. This report does not claim certified volume, mold readiness, or physical accuracy; AI visual references are non-authoritative.",
            "",
        ]
    )
    return "\n".join(lines)


def _summarize_artifact(
    context: MeasurementReportContext,
    artifact: MeasurementArtifact,
) -> dict[str, object]:
    if not isinstance(
        artifact,
        (
            BoundingDimensions,
            CapacityEstimate,
            CrossSectionMeasurement,
            HorizontalSection,
            MeasurementUncertaintyReport,
            NeckFinishCandidateSet,
            TwoPointDistanceMeasurement,
            VerticalProfile,
        ),
    ):
        raise MeasurementReportError("report_artifact_type_unsupported")
    source_geometry_id = artifact.source_geometry_id
    normalized_revision = artifact.normalized_geometry_revision
    scale_id = artifact.scale_provenance_id
    scale_state = artifact.scale_state
    if (
        source_geometry_id != context.source_geometry_id
        or normalized_revision != context.normalized_geometry_revision
        or scale_id != context.scale_provenance_id
        or scale_state is not context.scale_state
    ):
        raise MeasurementReportError("report_mixed_or_stale_artifact_parent")
    artifact_id = _artifact_id(artifact)
    if not isinstance(artifact_id, str) or not _SAFE_ID.fullmatch(artifact_id):
        raise MeasurementReportError("report_artifact_id_invalid")

    if isinstance(artifact, BoundingDimensions):
        artifact_type = "bounding_dimensions"
        artifact_id = artifact.measurement_id
        method = artifact.method_version
        units = artifact.coordinate_unit
        summary: dict[str, object] = {
            "dimensions": {
                "height": artifact.height,
                "width": artifact.width,
                "depth": artifact.depth,
            }
        }
        uncertainty = _pick(
            artifact.uncertainty_inputs,
            "scale_factor_uncertainty",
            "scale_factor_uncertainty_unit",
            "propagation_status",
        )
    elif isinstance(artifact, TwoPointDistanceMeasurement):
        artifact_type = "two_point_distance"
        artifact_id = artifact.measurement_id
        method = "normalized_two_point_distance_v1"
        units = artifact.coordinate_unit
        summary = {"distance": artifact.distance}
        uncertainty = {
            "scale_factor_uncertainty": artifact.scale_factor_uncertainty,
            "scale_factor_uncertainty_unit": artifact.scale_factor_uncertainty_unit,
            "uncertainty_propagated": False,
        }
    elif isinstance(artifact, CrossSectionMeasurement):
        artifact_type = "cross_section"
        artifact_id = artifact.measurement_id
        method = artifact.method_version
        units = artifact.coordinate_unit
        summary = {
            "center_z": artifact.center[2],
            "radii": {"major": artifact.major_radius, "minor": artifact.minor_radius},
            "diameters": {"major": artifact.major_diameter, "minor": artifact.minor_diameter},
            "rms_radial_residual": artifact.rms_radial_residual,
            "maximum_radial_residual": artifact.maximum_radial_residual,
        }
        uncertainty = {
            "scale_factor_uncertainty": artifact.scale_factor_uncertainty,
            "scale_factor_uncertainty_unit": artifact.scale_factor_uncertainty_unit,
            "fit_uncertainty_interval_estimated": False,
        }
    elif isinstance(artifact, HorizontalSection):
        artifact_type = "horizontal_section"
        artifact_id = artifact.section_id
        method = artifact.method_version
        units = artifact.coordinate_unit
        summary = {
            "requested_z": artifact.requested_z,
            "z_range": list(artifact.z_range),
            "slab_half_width": artifact.slab_half_width,
            "sample_count": len(artifact.points),
        }
        uncertainty = {"surface_interpolation_performed": False}
    elif isinstance(artifact, VerticalProfile):
        artifact_type = "vertical_profile"
        artifact_id = artifact.profile_id
        method = artifact.method_version
        units = artifact.coordinate_unit
        summary = {
            "horizontal_range": list(artifact.horizontal_range),
            "vertical_range": list(artifact.vertical_range),
            "sample_count": len(artifact.samples),
        }
        uncertainty = {"smoothing_performed": False, "outline_interpolation_performed": False}
    elif isinstance(artifact, NeckFinishCandidateSet):
        artifact_type = "neck_finish_candidates"
        artifact_id = artifact.result_id
        method = "supported_narrow_region_candidates_v1"
        units = artifact.coordinate_unit
        summary = {
            "baseline_radius": artifact.baseline_radius,
            "candidate_count": len(artifact.candidates),
            "candidates": [
                {
                    "rank": item.rank,
                    "candidate_type": item.candidate_type,
                    "section_z_range": list(item.section_z_range),
                    "major_diameter": item.major_diameter,
                    "minor_diameter": item.minor_diameter,
                    "height": item.height,
                    "review_required": item.review_required,
                    "ambiguity_review_required": item.ambiguity_review_required,
                }
                for item in artifact.candidates
            ],
        }
        uncertainty = {"candidate_uncertainty_is_confidence_interval": False}
    elif isinstance(artifact, CapacityEstimate):
        artifact_type = "capacity_estimate"
        artifact_id = artifact.estimate_id
        method = artifact.method_version
        units = artifact.capacity_unit
        summary = {
            "capacity_estimate": artifact.capacity,
            "source_volume": artifact.source_volume,
            "source_volume_unit": artifact.source_volume_unit,
            "interior_representation_id": artifact.interior_representation_id,
            "assumption_evidence_id": artifact.assumption_evidence_id,
            "certified_volume_claimed": False,
        }
        uncertainty = _pick(
            artifact.uncertainty_inputs,
            "scale_factor_uncertainty",
            "scale_factor_uncertainty_unit",
            "scale_uncertainty_propagated_to_volume",
            "mesh_discretization_uncertainty",
            "interior_shape_and_closure",
            "self_intersection_validation",
            "confidence_interval_estimated",
        )
    else:
        assert isinstance(artifact, MeasurementUncertaintyReport)
        artifact_type = "measurement_uncertainty"
        artifact_id = artifact.report_id
        method = "independent_standard_uncertainty_rss_scale_power_v1"
        units = artifact.estimate_unit
        summary = {
            "measurement_id": artifact.measurement_id,
            "estimate": artifact.estimate,
            "uncertainty": artifact.propagated_standard_uncertainty,
            "uncertainty_status": artifact.uncertainty_status,
            "estimate_display": artifact.estimate_display,
            "uncertainty_display": artifact.uncertainty_display,
        }
        uncertainty = {
            "components": [
                _pick(
                    item,
                    "name",
                    "value",
                    "unit",
                    "status",
                    "method",
                    "input_factor_unit",
                )
                for item in artifact.components
            ]
        }

    return {
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "method_version": method,
        "units": units,
        "summary": summary,
        "uncertainty": uncertainty,
        "authority_class": (
            "EXPLICIT_INTERIOR_ASSUMPTION"
            if isinstance(artifact, CapacityEstimate)
            else "OBJECT_CAPTURE_GEOMETRY"
        ),
        "generated": False,
        "certified_claimed": False,
        "mold_ready_claimed": False,
    }


def _summarize_modeled_closure_dimensions(
    context: MeasurementReportContext,
    scan_master: ScanMasterRevision | None,
    design_model: DesignModelRevision | None,
    *,
    expected_scan_master_revision_id: str | None,
    expected_design_model_revision_id: str | None,
) -> tuple[dict[str, object], ...]:
    supplied = (
        scan_master,
        design_model,
        expected_scan_master_revision_id,
        expected_design_model_revision_id,
    )
    if all(item is None for item in supplied):
        return ()
    if (
        not isinstance(scan_master, ScanMasterRevision)
        or not isinstance(design_model, DesignModelRevision)
        or not isinstance(expected_scan_master_revision_id, str)
        or not isinstance(expected_design_model_revision_id, str)
    ):
        raise MeasurementReportError("modeled_closure_parent_arguments_incomplete")
    digest = mesh_sha256(scan_master.mesh)
    manifest = scan_master.manifest
    if (
        scan_master.revision_id != expected_scan_master_revision_id
        or manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != digest
        or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or manifest.get("mold_use_authorized") is not False
    ):
        raise MeasurementReportError("modeled_closure_scan_master_stale_or_unauthorized")
    if (
        design_model.revision_id != expected_design_model_revision_id
        or design_model.project_id != scan_master.project_id
        or design_model.project_id != context.project_id
        or design_model.fitted_to_scan_master_revision_id != scan_master.revision_id
        or design_model.scan_master_geometry_sha256 != digest
        or design_model.scale_state.value != manifest.get("scale_state")
        or design_model.scale_provenance_id != manifest.get("scale_provenance_id")
        or design_model.scale_state is not context.scale_state
        or (
            context.scale_state is not ScaleState.RELATIVE
            and design_model.scale_provenance_id != context.scale_provenance_id
        )
        or design_model.coordinate_unit != context.coordinate_unit
        or design_model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or design_model.mold_use_authorized is not False
    ):
        raise MeasurementReportError("modeled_closure_design_model_parent_or_scale_mismatch")
    features = {item.feature_id: item for item in design_model.features}
    provenance = manifest.get("scale_provenance")
    scale_uncertainty = provenance.get("uncertainty") if isinstance(provenance, Mapping) else None
    if scale_uncertainty is not None and not isinstance(scale_uncertainty, Mapping):
        raise MeasurementReportError("modeled_closure_scale_uncertainty_invalid")
    results: list[dict[str, object]] = []
    for parameter in design_model.parameters:
        if parameter.value_type is not ParameterType.OBJECT:
            continue
        value = parameter.as_dict()["value"]
        if not isinstance(value, dict):
            continue
        contract = value.get("contract")
        if not isinstance(contract, str) or contract not in {
            "packlab.screw-cap-exterior-fit.v1",
            "packlab.flip-top-exterior.v1",
        }:
            continue
        try:
            result = _summarize_closure_parameter(
                parameter,
                value,
                str(contract),
                features,
                design_model,
                scan_master,
                digest,
                scale_uncertainty,
            )
        except (KeyError, TypeError, ValueError) as error:
            raise MeasurementReportError("modeled_closure_parameter_invalid") from error
        results.append(result)
    if not results:
        raise MeasurementReportError("modeled_closure_dimensions_missing")
    return tuple(
        sorted(results, key=lambda item: (str(item["feature_id"]), str(item["parameter_id"])))
    )


def _summarize_closure_parameter(
    parameter: DesignModelParameter,
    value: dict[str, object],
    contract: str,
    features: dict[str, DesignModelFeatureReference],
    design_model: DesignModelRevision,
    scan_master: ScanMasterRevision,
    geometry_digest: str,
    scale_uncertainty: Mapping[str, object] | None,
) -> dict[str, object]:
    feature_id = value.get("feature_id")
    component_id = value.get("component_id")
    feature = features.get(feature_id) if isinstance(feature_id, str) else None
    if (
        feature is None
        or feature.feature_kind is not FeatureKind.CAP
        or feature.component_id != component_id
        or value.get("review_required") is not True
        or value.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
        or value.get("mold_use_authorized") is not False
    ):
        raise ValueError("closure parameter feature or authority invalid")
    captured_ids: dict[str, list[str]]
    fit_evidence: dict[str, object]
    dimensions: dict[str, float]
    if contract == "packlab.screw-cap-exterior-fit.v1":
        if (
            value.get("thread_standard_inferred") is not False
            or value.get("internal_thread_geometry_inferred") is not False
            or value.get("seal_performance_inferred") is not False
            or value.get("manufacturing_dimensions_inferred") is not False
        ):
            raise ValueError("cylindrical closure has unsupported claims")
        raw_dimensions = value.get("parameters")
        if not isinstance(raw_dimensions, dict):
            raise ValueError("cylindrical dimensions missing")
        dimensions = {
            "exterior_diameter": _positive_dimension(
                raw_dimensions.get("screw_cap_exterior_diameter")
            ),
            "exterior_height": _positive_dimension(raw_dimensions.get("screw_cap_exterior_height")),
        }
        measurement_ids = value.get("section_measurement_ids")
        if not isinstance(measurement_ids, list) or not measurement_ids:
            raise ValueError("cylindrical fit support missing")
        captured_ids = {"cylindrical_exterior_fit": _safe_measurement_ids(measurement_ids)}
        fit_evidence = {
            "maximum_radial_residual": _finite_nonnegative(value.get("maximum_radial_residual")),
            "rms_radial_residual": _finite_nonnegative(value.get("rms_radial_residual")),
            "support_section_count": len(measurement_ids),
            "support_point_count": _positive_integer(value.get("support_point_count")),
            "fit_method": value.get("fit_method"),
        }
        closure_kind = "cylindrical_exterior"
    else:
        for key in (
            "latch_inferred",
            "seal_performance_inferred",
            "internal_mechanism_inferred",
            "wall_thickness_inferred",
            "manufacturing_dimensions_inferred",
        ):
            if value.get(key) is not False:
                raise ValueError("flip-top closure has unsupported claims")
        base, base_support, base_ids = _flip_top_region(value, "base")
        lid, lid_support, lid_ids = _flip_top_region(value, "lid_envelope")
        dimensions = {
            "base_diameter": base["diameter"],
            "base_supported_z_span": base["height"],
            "lid_envelope_diameter": lid["diameter"],
            "lid_envelope_supported_z_span": lid["height"],
        }
        captured_ids = {"base": base_ids, "lid_envelope": lid_ids}
        fit_evidence = {"base": base_support, "lid_envelope": lid_support}
        closure_kind = "flip_top_exterior"
    if value.get("parameter_unit", value.get("coordinate_unit")) != design_model.coordinate_unit:
        raise ValueError("closure parameter unit mismatch")
    return {
        "artifact_type": "parametric_closure_dimensions",
        "artifact_id": parameter.parameter_id,
        "source_kind": "PARAMETRIC_DESIGN_MODEL",
        "design_model_revision_id": design_model.revision_id,
        "parameter_id": parameter.parameter_id,
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": geometry_digest,
        "scale_state": design_model.scale_state.value,
        "scale_provenance_id": design_model.scale_provenance_id,
        "coordinate_unit": design_model.coordinate_unit,
        "feature_id": feature_id,
        "closure_kind": closure_kind,
        "dimensions": [
            {"name": key, "value": dimensions[key], "unit": design_model.coordinate_unit}
            for key in sorted(dimensions)
        ],
        "captured_fit_support": {
            "source_kind": "CAPTURED_CROSS_SECTION_MEASUREMENTS",
            "measurement_ids": captured_ids,
            "fit_evidence": fit_evidence,
        },
        "uncertainty": {
            "scale_uncertainty": None
            if scale_uncertainty is None
            else _plain_json(scale_uncertainty),
            "scale_uncertainty_propagated_to_dimensions": False,
            "fit_confidence_interval_estimated": False,
        },
        "review_required": True,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "certified_claimed": False,
        "mold_ready_claimed": False,
    }


def _flip_top_region(
    value: dict[str, object], name: str
) -> tuple[dict[str, float], dict[str, object], list[str]]:
    region = value.get(name)
    if not isinstance(region, dict):
        raise ValueError("flip-top region missing")
    dimensions = {
        "diameter": _positive_dimension(region.get("diameter")),
    }
    z_range = region.get("z_range")
    if not isinstance(z_range, list) or len(z_range) != 2:
        raise ValueError("flip-top range invalid")
    low, high = (_finite_number(item) for item in z_range)
    dimensions["height"] = high - low
    if dimensions["height"] <= 0.0:
        raise ValueError("flip-top height invalid")
    ids = region.get("measurement_ids")
    support = region.get("support")
    if not isinstance(ids, list) or not ids or not isinstance(support, dict):
        raise ValueError("flip-top fit support missing")
    return (
        dimensions,
        {
            "section_count": _positive_integer(support.get("section_count")),
            "point_count": _positive_integer(support.get("point_count")),
            "maximum_radial_residual": _finite_nonnegative(support.get("maximum_radial_residual")),
            "rms_radial_residual": _finite_nonnegative(support.get("rms_radial_residual")),
            "scale_uncertainty": support.get("scale_uncertainty"),
            "scale_uncertainty_unit": support.get("scale_uncertainty_unit"),
        },
        _safe_measurement_ids(ids),
    )


def _safe_measurement_ids(values: list[object]) -> list[str]:
    safe_ids: list[str] = []
    for item in values:
        if not isinstance(item, str) or not _SAFE_ID.fullmatch(item):
            raise ValueError("captured measurement ID invalid")
        safe_ids.append(item)
    return sorted(safe_ids)


def _finite_number(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("dimension value invalid")
    return float(value)


def _positive_dimension(value: object) -> float:
    number = _finite_number(value)
    if number <= 0.0:
        raise ValueError("dimension must be positive")
    return number


def _finite_nonnegative(value: object) -> float:
    number = _finite_number(value)
    if number < 0.0:
        raise ValueError("fit residual invalid")
    return number


def _positive_integer(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError("support count invalid")
    return value


def _plain_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _plain_json(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain_json(item) for item in value]
    return value


def _artifact_id(artifact: MeasurementArtifact) -> str:
    if isinstance(
        artifact, (BoundingDimensions, CrossSectionMeasurement, TwoPointDistanceMeasurement)
    ):
        return artifact.measurement_id
    if isinstance(artifact, HorizontalSection):
        return artifact.section_id
    if isinstance(artifact, VerticalProfile):
        return artifact.profile_id
    if isinstance(artifact, CapacityEstimate):
        return artifact.estimate_id
    if isinstance(artifact, NeckFinishCandidateSet):
        return artifact.result_id
    return artifact.report_id


def _pick(values: object, *allowed_keys: str) -> dict[str, object]:
    if not isinstance(values, Mapping):
        return {}
    return {key: values[key] for key in allowed_keys if key in values}
