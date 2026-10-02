"""Persistable calibration scale provenance and fail-closed promotion rules."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from datetime import datetime

from ..reconstruction import ScaleState
from .reconstruction_scale import (
    ReconstructionScaleEstimate,
    ReconstructionScaleObservation,
    _observation_id,
)

SCALE_PROVENANCE_VERSION = "scale_provenance_v1"
SCALE_PROVENANCE_CONTRACT = "packlab.scale-provenance.v1"
_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ScaleProvenanceError(ValueError):
    """Raised when scale evidence is incomplete, stale, or unauthorized."""


@dataclass(frozen=True, slots=True)
class VerifiedPhysicalReference:
    reference_id: str
    reference_digest: str
    marker_id: int
    measured_side_length_mm: float

    def __post_init__(self) -> None:
        if not isinstance(self.reference_id, str) or not self.reference_id.strip():
            raise ScaleProvenanceError("verified_reference_id_required")
        if not isinstance(self.reference_digest, str) or not _SHA256.fullmatch(
            self.reference_digest
        ):
            raise ScaleProvenanceError("verified_reference_digest_invalid")
        if (
            not isinstance(self.marker_id, int)
            or isinstance(self.marker_id, bool)
            or self.marker_id < 0
        ):
            raise ScaleProvenanceError("verified_reference_marker_id_invalid")
        if not _positive_finite(self.measured_side_length_mm):
            raise ScaleProvenanceError("verified_reference_measurement_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "reference_id": self.reference_id,
            "reference_digest": self.reference_digest,
            "marker_id": self.marker_id,
            "measured_side_length": self.measured_side_length_mm,
            "unit": "mm",
        }


@dataclass(frozen=True, slots=True)
class ScalePromotionEvidence:
    evidence_class: str
    source_type: str
    verification_record_id: str
    verification_record_sha256: str
    verification_status: str
    verification_timestamp_utc: str
    operator_id: str
    instrument_reference: str
    owner_measurement_complete: bool
    verified_references: tuple[VerifiedPhysicalReference, ...]

    def __post_init__(self) -> None:
        for name in (
            "evidence_class",
            "source_type",
            "verification_record_id",
            "verification_status",
            "verification_timestamp_utc",
            "operator_id",
            "instrument_reference",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ScaleProvenanceError(f"promotion_{name}_required")
        if not isinstance(self.verification_record_sha256, str) or not _SHA256.fullmatch(
            self.verification_record_sha256
        ):
            raise ScaleProvenanceError("promotion_verification_record_digest_invalid")
        if not isinstance(self.owner_measurement_complete, bool):
            raise ScaleProvenanceError("promotion_owner_measurement_flag_invalid")
        _validate_timestamp(self.verification_timestamp_utc)
        if not self.verified_references or len(
            {item.reference_id for item in self.verified_references}
        ) != len(self.verified_references):
            raise ScaleProvenanceError("promotion_verified_references_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_class": self.evidence_class,
            "source_type": self.source_type,
            "verification_record_id": self.verification_record_id,
            "verification_record_sha256": self.verification_record_sha256,
            "verification_status": self.verification_status,
            "verification_timestamp_utc": self.verification_timestamp_utc,
            "operator_id": self.operator_id,
            "instrument_reference": self.instrument_reference,
            "owner_measurement_complete": self.owner_measurement_complete,
            "verified_references": [item.as_dict() for item in self.verified_references],
        }


@dataclass(frozen=True, slots=True)
class ScaleProvenance:
    provenance_id: str
    source_method: str
    calibration_observation_ids: tuple[str, ...]
    physical_references: tuple[dict[str, object], ...]
    estimated_scale_factor_mm_per_reconstruction_unit: float | None
    residuals: tuple[dict[str, object], ...]
    rejected_observations: tuple[dict[str, str], ...]
    algorithm_version: str
    outlier_policy_version: str
    input_reconstruction_revision: str
    camera_solution_revision: str
    uncertainty: dict[str, object] | None
    created_at_utc: str
    actor_id: str
    process_id: str
    scale_state: ScaleState
    promotion_evidence: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.scale_state, ScaleState):
            raise ScaleProvenanceError("scale_provenance_state_invalid")
        if self.scale_state is ScaleState.RELATIVE:
            if self.estimated_scale_factor_mm_per_reconstruction_unit is not None:
                raise ScaleProvenanceError("relative_scale_provenance_cannot_carry_factor")
        elif not _positive_finite(self.estimated_scale_factor_mm_per_reconstruction_unit):
            raise ScaleProvenanceError("metric_scale_provenance_requires_positive_factor")
        if self.scale_state is ScaleState.METRIC_VERIFIED:
            if (
                not isinstance(self.promotion_evidence, dict)
                or self.promotion_evidence.get("evidence_class") != "accepted_owner_physical"
            ):
                raise ScaleProvenanceError("verified_scale_provenance_requires_owner_evidence")
        elif self.promotion_evidence is not None:
            raise ScaleProvenanceError("unverified_scale_provenance_cannot_have_promotion_evidence")
        identity = self.as_dict()
        identity.pop("provenance_id")
        expected = "scale-provenance:" + _digest(identity)
        if self.provenance_id != expected:
            raise ScaleProvenanceError("scale_provenance_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": SCALE_PROVENANCE_CONTRACT,
            "version": SCALE_PROVENANCE_VERSION,
            "provenance_id": self.provenance_id,
            "source_method": self.source_method,
            "calibration_observation_ids": list(self.calibration_observation_ids),
            "physical_references": [dict(item) for item in self.physical_references],
            "estimated_scale_factor": self.estimated_scale_factor_mm_per_reconstruction_unit,
            "scale_factor_unit": "mm_per_reconstruction_unit",
            "residuals": [dict(item) for item in self.residuals],
            "rejected_observations": [dict(item) for item in self.rejected_observations],
            "algorithm_version": self.algorithm_version,
            "outlier_policy_version": self.outlier_policy_version,
            "input_reconstruction_revision": self.input_reconstruction_revision,
            "camera_solution_revision": self.camera_solution_revision,
            "uncertainty": None if self.uncertainty is None else dict(self.uncertainty),
            "created_at_utc": self.created_at_utc,
            "actor_process_provenance": {
                "actor_id": self.actor_id,
                "process_id": self.process_id,
            },
            "scale_state": self.scale_state.value,
            "promotion_evidence": (
                None if self.promotion_evidence is None else dict(self.promotion_evidence)
            ),
            "ai_visual_reference_measurement_authority": False,
        }


def create_scale_provenance(
    estimate: ReconstructionScaleEstimate,
    observations: tuple[ReconstructionScaleObservation, ...],
    *,
    reconstruction_revision: str,
    camera_solution_revision: str,
    created_at_utc: str,
    actor_id: str,
    process_id: str,
) -> ScaleProvenance:
    """Bind an estimate and every accepted/rejected source reference in one record."""

    _validate_timestamp(created_at_utc)
    _require_text(actor_id, "scale_actor_id_required")
    _require_text(process_id, "scale_process_id_required")
    algorithm_version = estimate.provenance.get("math_version")
    outlier_policy_version = estimate.provenance.get("outlier_policy_version")
    if (
        not isinstance(reconstruction_revision, str)
        or not reconstruction_revision.strip()
        or not isinstance(camera_solution_revision, str)
        or not camera_solution_revision.strip()
        or not isinstance(algorithm_version, str)
        or not algorithm_version.strip()
        or not isinstance(outlier_policy_version, str)
        or not outlier_policy_version.strip()
    ):
        raise ScaleProvenanceError("scale_estimate_provenance_incomplete")
    for parent_name, supplied_parent in (
        ("reconstruction_revision", reconstruction_revision),
        ("camera_solution_revision", camera_solution_revision),
    ):
        estimate_parent = estimate.provenance.get(parent_name)
        if estimate_parent is not None and estimate_parent != supplied_parent:
            raise ScaleProvenanceError("scale_estimate_parent_revision_mismatch")
    supplied = {
        _observation_id(item.reconstructed_geometry.observation): item for item in observations
    }
    rejected = tuple(_parse_rejection(item) for item in estimate.observations_rejected)
    known_ids = set(estimate.observations_used) | {item["observation_id"] for item in rejected}
    if not known_ids.issubset(supplied):
        raise ScaleProvenanceError("scale_estimate_observation_binding_incomplete")
    if estimate.status == "estimated":
        if (
            estimate.metric_state != "METRIC_UNVERIFIED"
            or not _positive_finite(estimate.reconstruction_units_to_mm)
            or not _positive_finite(estimate.uncertainty_mm_per_reconstruction_unit)
        ):
            raise ScaleProvenanceError("scale_estimate_state_or_factor_invalid")
        state = ScaleState.METRIC_UNVERIFIED
        uncertainty: dict[str, object] | None = {
            "representation": "standard_uncertainty_mm_per_reconstruction_unit",
            "value": estimate.uncertainty_mm_per_reconstruction_unit,
        }
    elif estimate.status == "rejected":
        if (
            estimate.reconstruction_units_to_mm is not None
            or estimate.uncertainty_mm_per_reconstruction_unit is not None
        ):
            raise ScaleProvenanceError("rejected_scale_estimate_must_not_have_factor")
        state = ScaleState.RELATIVE
        uncertainty = None
    else:
        raise ScaleProvenanceError("scale_estimate_status_invalid")
    references: list[dict[str, object]] = []
    for observation_id in sorted(supplied):
        item = supplied[observation_id]
        reference = item.physical_reference
        references.append(
            {
                "observation_id": observation_id,
                "marker_id": reference.marker_id,
                "reference_id": reference.reference_id,
                "reference_digest": reference.reference_digest,
                "value": reference.side_length,
                "unit": reference.unit,
                "uncertainty_mm": reference.uncertainty_mm,
                "evidence_class": reference.evidence_class,
                "used_in_estimate": observation_id in estimate.observations_used,
            }
        )
    body: dict[str, object] = {
        "contract": SCALE_PROVENANCE_CONTRACT,
        "version": SCALE_PROVENANCE_VERSION,
        "source_method": "camera_bound_marker_3d_scale_estimation",
        "calibration_observation_ids": list(estimate.observations_used),
        "physical_references": references,
        "estimated_scale_factor": estimate.reconstruction_units_to_mm,
        "scale_factor_unit": "mm_per_reconstruction_unit",
        "residuals": [dict(item) for item in estimate.residuals],
        "rejected_observations": list(rejected),
        "algorithm_version": algorithm_version,
        "outlier_policy_version": outlier_policy_version,
        "input_reconstruction_revision": reconstruction_revision,
        "camera_solution_revision": camera_solution_revision,
        "uncertainty": uncertainty,
        "created_at_utc": created_at_utc,
        "actor_process_provenance": {"actor_id": actor_id, "process_id": process_id},
        "scale_state": state.value,
        "promotion_evidence": None,
        "ai_visual_reference_measurement_authority": False,
    }
    provenance_id = "scale-provenance:" + _digest(body)
    return ScaleProvenance(
        provenance_id,
        "camera_bound_marker_3d_scale_estimation",
        tuple(estimate.observations_used),
        tuple(references),
        estimate.reconstruction_units_to_mm,
        tuple(dict(item) for item in estimate.residuals),
        rejected,
        algorithm_version,
        outlier_policy_version,
        reconstruction_revision,
        camera_solution_revision,
        uncertainty,
        created_at_utc,
        actor_id,
        process_id,
        state,
    )


def promote_scale_provenance(
    provenance: ScaleProvenance,
    evidence: ScalePromotionEvidence,
) -> ScaleProvenance:
    """Promote only with accepted owner-measured physical reference evidence."""

    if (
        provenance.scale_state is not ScaleState.METRIC_UNVERIFIED
        or provenance.estimated_scale_factor_mm_per_reconstruction_unit is None
    ):
        raise ScaleProvenanceError("scale_promotion_requires_unverified_estimate")
    if (
        evidence.evidence_class != "accepted_owner_physical"
        or evidence.source_type != "owner_controlled_physical_record"
        or evidence.verification_status != "ACCEPTED_FOR_CAPTURE"
        or evidence.owner_measurement_complete is not True
    ):
        raise ScaleProvenanceError("scale_promotion_requires_accepted_owner_physical_evidence")
    used_refs = [
        item for item in provenance.physical_references if item.get("used_in_estimate") is True
    ]
    verified = {item.reference_id: item for item in evidence.verified_references}
    if not used_refs or any(
        reference.get("evidence_class") != "accepted_owner_physical"
        or not isinstance(reference.get("reference_id"), str)
        or reference["reference_id"] not in verified
        or verified[reference["reference_id"]].reference_digest != reference.get("reference_digest")
        or verified[reference["reference_id"]].marker_id != reference.get("marker_id")
        or verified[reference["reference_id"]].measured_side_length_mm != reference.get("value")
        for reference in used_refs
    ):
        raise ScaleProvenanceError("scale_promotion_reference_not_owner_verified")
    promotion = evidence.as_dict()
    body = provenance.as_dict()
    body["scale_state"] = ScaleState.METRIC_VERIFIED.value
    body["promotion_evidence"] = promotion
    body.pop("provenance_id")
    provenance_id = "scale-provenance:" + _digest(body)
    return ScaleProvenance(
        provenance_id,
        provenance.source_method,
        provenance.calibration_observation_ids,
        provenance.physical_references,
        provenance.estimated_scale_factor_mm_per_reconstruction_unit,
        provenance.residuals,
        provenance.rejected_observations,
        provenance.algorithm_version,
        provenance.outlier_policy_version,
        provenance.input_reconstruction_revision,
        provenance.camera_solution_revision,
        provenance.uncertainty,
        provenance.created_at_utc,
        provenance.actor_id,
        provenance.process_id,
        ScaleState.METRIC_VERIFIED,
        promotion,
    )


def append_scale_provenance_revision(
    history: object,
    provenance: ScaleProvenance,
    *,
    current_reconstruction_revision: str,
) -> list[dict[str, object]]:
    """Return append-only project metadata after checking the reconstruction parent."""

    if provenance.input_reconstruction_revision != current_reconstruction_revision:
        raise ScaleProvenanceError("scale_provenance_stale_reconstruction_parent")
    if not isinstance(history, list):
        raise ScaleProvenanceError("scale_provenance_history_malformed")
    result: list[dict[str, object]] = []
    for previous in history:
        if not isinstance(previous, dict) or previous.get("contract") != SCALE_PROVENANCE_CONTRACT:
            raise ScaleProvenanceError("scale_provenance_history_malformed")
        result.append(dict(previous))
    if any(previous.get("provenance_id") == provenance.provenance_id for previous in result):
        raise ScaleProvenanceError("scale_provenance_revision_already_exists")
    result.append(provenance.as_dict())
    return result


def serialize_scale_provenance(provenance: ScaleProvenance) -> bytes:
    return json.dumps(
        provenance.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _parse_rejection(value: str) -> dict[str, str]:
    observation_id, separator, reason = value.partition(":")
    if not separator or not _SHA256.fullmatch(observation_id) or not reason:
        raise ScaleProvenanceError("scale_estimate_rejection_record_malformed")
    return {"observation_id": observation_id, "reason": reason}


def _validate_timestamp(value: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ScaleProvenanceError("scale_created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ScaleProvenanceError("scale_created_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ScaleProvenanceError("scale_created_at_must_be_utc_z")


def _require_text(value: str, error_code: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ScaleProvenanceError(error_code)


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()
