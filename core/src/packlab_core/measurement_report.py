"""Deterministic privacy-conscious export for PackLab measurement artifacts."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass

from .bounding_dimensions import BoundingDimensions
from .capacity_estimation import CapacityEstimate
from .cross_section_measurement import CrossSectionMeasurement
from .horizontal_section import HorizontalSection
from .measurement_uncertainty import MeasurementUncertaintyReport
from .neck_finish_candidates import NeckFinishCandidateSet
from .reconstruction import ScaleState
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
            "authority_and_limitations": {
                "authority_class": "OBJECT_CAPTURE_GEOMETRY_OR_EXPLICIT_INTERIOR_ASSUMPTION",
                "ai_visual_reference_authoritative": False,
                "certified_measurement_claimed": False,
                "mold_ready_claimed": False,
                "physical_accuracy_claimed": False,
                "private_raw_bytes_included": False,
                "ambient_identity_included": False,
            },
        }


def build_measurement_report(
    context: MeasurementReportContext,
    artifacts: tuple[MeasurementArtifact, ...],
) -> MeasurementReport:
    """Build a deterministic report from same-parent PackLab measurement objects."""

    if not isinstance(artifacts, tuple) or not artifacts:
        raise MeasurementReportError("report_artifacts_must_be_nonempty_immutable_tuple")
    summaries = tuple(_summarize_artifact(context, artifact) for artifact in artifacts)
    ids = tuple(str(item["artifact_id"]) for item in summaries)
    if len(set(ids)) != len(ids):
        raise MeasurementReportError("report_duplicate_artifact_id")
    ordered = tuple(
        sorted(summaries, key=lambda item: (str(item["artifact_type"]), str(item["artifact_id"])))
    )
    return MeasurementReport(context, ordered)


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
