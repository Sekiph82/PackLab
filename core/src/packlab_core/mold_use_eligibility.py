"""PL-0224 machine-checkable mould-use exclusion conditions.

``evaluate_mold_use_eligibility`` reports every condition under which PackLab measurements
must NOT be used for mould manufacturing (see
docs/development/PL-0224_MOLD_USE_EXCLUSION_CONDITIONS.md). It only reports eligibility; it
never authorizes mould use, and its output always carries ``mold_use_authorized: False``.

Authority is read from the actual ``ScanMasterRevision`` / ``DesignModelRevision`` objects
and checked against an allow-list (fail closed). Accepted thresholds are re-derived through
``accept_threshold_proposal`` from the physical inputs, never trusted as a dict. The PL-0222
and PL-0223 reports are digest-checked for integrity only (unkeyed SHA-256, not
authenticity). The hard blocker today is ``PL0220_PHYSICAL_BENCHMARK_STATUS``: while it is
deferred, ``physical_validation_deferred`` always applies and threshold acceptance raises.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from . import acceptance_thresholds as thresholds
from . import print_scale_sensitivity as print_scale
from . import repeat_scan_reproducibility as repeatability
from .design_model import DesignModelParentKind, DesignModelRevision, PackageFamily
from .design_model_binding import ParentBindingStatus
from .flexible_pack_authority import is_flexible_pack_model
from .physical_accuracy_benchmark import REQUIRED_BENCHMARK_CATEGORIES, _safe_token
from .reconstruction import ReconstructionBackendId, ScaleState
from .scan_master import ScanMasterRevision
from .visual_material_library import MaterialFamily

ELIGIBILITY_CONTRACT = "packlab.mold-use-eligibility.v1"
ELIGIBLE = "ELIGIBLE"
NOT_ELIGIBLE = "NOT_ELIGIBLE"
# Allow-list (fail closed): authority class -> whether a DesignModelRevision is required.
MOLD_RELEVANT_AUTHORITY = {"SCAN_MASTER": False, "DESIGN_MODEL": True}
# Known visual/preview classes, reported as an extra explanation (already not allow-listed).
VISUAL_AUTHORITY_CLASSES = frozenset(
    {
        "AI_VISUAL_REFERENCE",
        "AI_DIMENSION_FIT_PROPOSAL",
        "AR_VISUAL_REFERENCE_ONLY",
        "NON_CERTIFIED_VISUAL_REFERENCE",
        "PREVIEW_PROXY",
        "DESIGN_MODEL_WITH_PREVIEW_PROXY",
        "DESIGN_MODEL_OPERATION_WITH_PREVIEW_PROXY",
        "VISUAL_PRODUCT_CONTENT_APPEARANCE_ASSIGNMENT",
    }
)
RIGID_PACKAGE_FAMILIES = frozenset(
    {
        PackageFamily.BOTTLE,
        PackageFamily.JAR,
        PackageFamily.CYLINDRICAL_CONTAINER,
        PackageFamily.JERRYCAN,
    }
)
# PET (clear/glossy) defeats photogrammetry (PL-0377); OTHER has no benchmark basis.
MATERIALS_WITH_BENCHMARK_BASIS = frozenset({MaterialFamily.HDPE, MaterialFamily.PP})
RULER_PASS = "WITHIN_PROVISIONAL_PRINT_TOLERANCE"
# Explicit allow-list of physical validation statuses (missing/unknown/DEFERRED all fail).
# No production code emits this value today: promote_scan_master and DesignModelRevision always
# write DEFERRED_OWNER_VALIDATION. Only an owner-recorded, reviewed validation may set it.
ACCEPTED_PHYSICAL_VALIDATION_STATUSES = frozenset({"OWNER_PHYSICAL_VALIDATION_ACCEPTED"})
# Benchmark categories that may justify a tolerance for each rigid package family.
FAMILY_BENCHMARK_CATEGORIES = {
    PackageFamily.BOTTLE: frozenset({"matte_bottle", "glossy_bottle"}),
    PackageFamily.JERRYCAN: frozenset({"jerrycan"}),
}

EXCLUSION_REASONS = (
    "physical_validation_deferred",
    "authority_not_allow_listed",
    "visual_reference_authority",
    "generated_asset",
    "not_scan_master_authority",
    "design_model_not_fitted_to_scan_master",
    "design_model_parent_binding_not_current",
    "package_family_flexible_tube_or_unknown",
    "material_pet_or_unknown",
    "reconstruction_backend_experimental_or_unknown",
    "scale_not_metric_verified",
    "scale_provenance_missing",
    "printed_mat_ruler_record_missing_or_unverified",
    "thresholds_not_accepted",
    "measurement_tolerance_unavailable",
    "measurement_subject_mismatch",
    "measurement_exceeds_accepted_tolerance",
    "partial_coverage",
    "surface_texture_qa_not_passed",
    "synthetic_or_simulation_data",
    "repeatability_not_established",
)


class MoldUseEligibilityError(ValueError):
    """Raised for malformed eligibility inputs."""


@dataclass(frozen=True, slots=True)
class MeasurementToleranceCheck:
    """One measurement to compare against the accepted group tolerance."""

    measurement_id: str
    category: str
    material: MaterialFamily
    dimension_kind: str
    expanded_uncertainty_mm: float | None

    def __post_init__(self) -> None:
        if not _safe_token(self.measurement_id):
            raise MoldUseEligibilityError("measurement_id_invalid")
        if self.category not in REQUIRED_BENCHMARK_CATEGORIES:
            raise MoldUseEligibilityError("measurement_category_unsupported")
        if not isinstance(self.material, MaterialFamily):
            raise MoldUseEligibilityError("measurement_material_invalid")
        if self.dimension_kind not in thresholds.DIMENSION_FEATURE_GROUPS:
            raise MoldUseEligibilityError("measurement_dimension_kind_unsupported")
        value = self.expanded_uncertainty_mm
        if value is not None and (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0.0
        ):
            raise MoldUseEligibilityError("measurement_expanded_uncertainty_invalid")


@dataclass(frozen=True, slots=True)
class ThresholdAcceptanceInputs:
    """Everything ``accept_threshold_proposal`` needs; eligibility re-runs it."""

    records: Sequence[thresholds.PhysicalAccuracyBenchmarkRecord]
    observations: Sequence[thresholds.BenchmarkMeasurementObservation]
    proposal: Mapping[str, object]
    acceptance: thresholds.OwnerThresholdAcceptance


@dataclass(frozen=True, slots=True)
class MoldUseEvidence:
    """Subject objects plus capture evidence. Every default fails closed."""

    authority_class: str
    scan_master: ScanMasterRevision | None = None
    design_model: DesignModelRevision | None = None
    design_model_parent_binding: ParentBindingStatus | None = None
    package_family: PackageFamily | None = None  # used when no Design Model is given
    material: MaterialFamily | None = None
    reconstruction_backend: ReconstructionBackendId | None = None
    print_scale_report: Mapping[str, object] | None = None
    threshold_inputs: ThresholdAcceptanceInputs | None = None
    measurements: tuple[MeasurementToleranceCheck, ...] = ()
    partial_coverage: bool = True
    # pre_reconstruction_qa photo_reports[*]["object_surface_texture"]["status"] values.
    object_surface_texture_statuses: tuple[str, ...] = ()
    simulation_only: bool = True
    repeatability_report: Mapping[str, object] | None = None


def evaluate_mold_use_eligibility(evidence: MoldUseEvidence) -> dict[str, object]:
    """Return NOT_ELIGIBLE with every applicable reason; never authorizes mould use."""

    if not isinstance(evidence, MoldUseEvidence):
        raise TypeError("MoldUseEvidence required")
    reasons: set[str] = set()
    scan = evidence.scan_master if isinstance(evidence.scan_master, ScanMasterRevision) else None
    model = (
        evidence.design_model if isinstance(evidence.design_model, DesignModelRevision) else None
    )
    manifest: Mapping[str, object] = scan.manifest if scan is not None else {}

    if thresholds.PL0220_PHYSICAL_BENCHMARK_STATUS != "OWNER_BENCHMARK_EVIDENCE_ACCEPTED":
        reasons.add("physical_validation_deferred")
    if manifest.get("physical_accuracy_validation_status") not in (
        ACCEPTED_PHYSICAL_VALIDATION_STATUSES
    ) or (
        model is not None
        and model.physical_accuracy_validation_status not in ACCEPTED_PHYSICAL_VALIDATION_STATUSES
    ):
        reasons.add("physical_validation_deferred")

    # Authority: fail-closed allow-list over the declared class and the actual objects.
    needs_model = MOLD_RELEVANT_AUTHORITY.get(evidence.authority_class)
    if needs_model is None or needs_model != (model is not None):
        reasons.add("authority_not_allow_listed")
    if evidence.authority_class in VISUAL_AUTHORITY_CLASSES:
        reasons.add("visual_reference_authority")
    if manifest.get("generated") is not None and manifest.get("generated") is not False:
        reasons.add("generated_asset")
    if scan is None or manifest.get("authority_class") != "SCAN_MASTER":
        reasons.add("not_scan_master_authority")
    if needs_model:
        if (
            model is None
            or model.parent_kind is not DesignModelParentKind.CAPTURED_SCAN_MASTER
            or scan is None
            or model.fitted_to_scan_master_revision_id != scan.revision_id
        ):
            reasons.add("design_model_not_fitted_to_scan_master")
        if evidence.design_model_parent_binding is not ParentBindingStatus.CURRENT:
            reasons.add("design_model_parent_binding_not_current")

    family = model.package_family if model is not None else evidence.package_family
    if family not in RIGID_PACKAGE_FAMILIES or (
        model is not None and is_flexible_pack_model(model)
    ):
        reasons.add("package_family_flexible_tube_or_unknown")
    if evidence.material not in MATERIALS_WITH_BENCHMARK_BASIS:
        reasons.add("material_pet_or_unknown")
    if evidence.reconstruction_backend is not ReconstructionBackendId.COLMAP_OPENMVS:
        reasons.add("reconstruction_backend_experimental_or_unknown")

    scale_states = {manifest.get("scale_state")}
    provenance_ids = {manifest.get("scale_provenance_id")}
    if model is not None:
        scale_states.add(model.scale_state.value)
        provenance_ids.add(model.scale_provenance_id)
    if scale_states != {ScaleState.METRIC_VERIFIED.value}:
        reasons.add("scale_not_metric_verified")
    if len(provenance_ids) != 1 or not all(isinstance(item, str) for item in provenance_ids):
        reasons.add("scale_provenance_missing")
    if not _ruler_verified(evidence.print_scale_report):
        reasons.add("printed_mat_ruler_record_missing_or_unverified")

    tolerances = _accepted_tolerances(evidence.threshold_inputs)
    if tolerances is None:
        reasons.add("thresholds_not_accepted")
    if not evidence.measurements:
        reasons.add("measurement_tolerance_unavailable")
    allowed_categories = (
        FAMILY_BENCHMARK_CATEGORIES.get(family, frozenset()) if family is not None else frozenset()
    )
    for item in evidence.measurements:
        if not isinstance(item, MeasurementToleranceCheck):
            raise MoldUseEligibilityError("measurement_check_invalid")
        # A measurement may only borrow a tolerance from the subject's own material/family.
        if item.material is not evidence.material or item.category not in allowed_categories:
            reasons.add("measurement_subject_mismatch")
        group = thresholds.DIMENSION_FEATURE_GROUPS[item.dimension_kind]
        limit = (tolerances or {}).get((item.category, item.material.value, group))
        if limit is None or item.expanded_uncertainty_mm is None:
            reasons.add("measurement_tolerance_unavailable")
        elif item.expanded_uncertainty_mm > limit:
            reasons.add("measurement_exceeds_accepted_tolerance")

    gaps = manifest.get("coverage_gaps")  # frozen to a tuple by ScanMasterRevision
    if evidence.partial_coverage is not False or not isinstance(gaps, (list, tuple)) or gaps:
        reasons.add("partial_coverage")
    statuses = evidence.object_surface_texture_statuses
    if not statuses or any(status != "pass" for status in statuses):
        reasons.add("surface_texture_qa_not_passed")
    if evidence.simulation_only is not False:
        reasons.add("synthetic_or_simulation_data")
    if not _repeatability_established(evidence.repeatability_report):
        reasons.add("repeatability_not_established")

    ordered = [reason for reason in EXCLUSION_REASONS if reason in reasons]
    body: dict[str, object] = {
        "contract": ELIGIBILITY_CONTRACT,
        "status": NOT_ELIGIBLE if ordered else ELIGIBLE,
        "reasons": ordered,
        "physical_benchmark_gate": thresholds.PL0220_PHYSICAL_BENCHMARK_STATUS,
        "scan_master_revision_id": scan.revision_id if scan is not None else None,
        "design_model_revision_id": model.revision_id if model is not None else None,
        # Eligibility is never authorization: qualified tooling engineering review, supplier
        # approval and explicit owner authorization remain external (V1 boundary statement).
        "mold_use_authorized": False,
    }
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return body | {"report_sha256": hashlib.sha256(encoded).hexdigest()}


def _accepted_tolerances(
    inputs: ThresholdAcceptanceInputs | None,
) -> dict[tuple[str, str, str], float] | None:
    if not isinstance(inputs, ThresholdAcceptanceInputs):
        return None
    try:
        accepted = thresholds.accept_threshold_proposal(
            inputs.records, inputs.observations, inputs.proposal, inputs.acceptance
        )
    except (thresholds.AcceptanceThresholdError, TypeError, KeyError, AttributeError):
        return None
    proposal = accepted.get("proposal")
    if (
        accepted.get("status") != thresholds.ACCEPTED
        or accepted.get("simulation_only") is not False
        or not isinstance(proposal, Mapping)
        or proposal.get("status") != thresholds.PROPOSED
        or proposal.get("simulation_only") is not False
    ):
        return None
    groups = proposal.get("groups")
    if not isinstance(groups, list):
        return None
    return {
        (str(g["category"]), str(g["material"]), str(g["feature_group"])): float(
            g["proposed_tolerance_mm"]
        )
        for g in groups
        if isinstance(g, Mapping) and g.get("status") == "THRESHOLD_PROPOSED"
    }


def _ruler_verified(report: Mapping[str, object] | None) -> bool:
    if report is None or report.get("contract") != print_scale.REPORT_CONTRACT:
        return False
    if not print_scale.report_digest_valid(report):
        return False
    check = report.get("owner_ruler_check")
    return (
        isinstance(check, Mapping)
        and check.get("status") == RULER_PASS
        and isinstance(check.get("record_reference"), str)
        and isinstance(check.get("instrument_reference"), str)
    )


def _repeatability_established(report: Mapping[str, object] | None) -> bool:
    # Integrity only: the PL-0222 report is always simulation_only today, so this fails.
    return (
        report is not None
        and report.get("contract") == repeatability.REPORT_CONTRACT
        and repeatability.report_digest_valid(report)
        and report.get("simulation_only") is False
        and report.get("physical_reproducibility_claim") is True
        and report.get("provisional_threshold_result") == "WITHIN_PROVISIONAL_THRESHOLDS"
    )
