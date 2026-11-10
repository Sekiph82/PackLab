"""PL-0414 advisory rescan/recapture decision tree over existing capture-QA evidence.

Maps a pre-reconstruction QA report and an optional recapture-sector report to an ordered
list of operator actions. It never mutates capture data, never accepts a scan and never
claims reconstruction quality or physical accuracy; an operator confirms every action.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from typing import Final

RESCAN_DECISION_CONTRACT: Final = "packlab.rescan-decision.v1"
# Fraction of texture-assessed views that must be low-texture before the whole object is
# routed to the PL-0399 surface-treatment review instead of photo retakes.
LOW_TEXTURE_VIEW_FRACTION: Final = 0.5

# Severity order; the first triggered action is the primary action.
ACTIONS: Final = (
    "stop_reimport_source",
    "full_rescan",
    "surface_treatment_review",
    "targeted_recapture",
    "retake_flagged_photos",
    "manual_review_insufficient_evidence",
    "proceed_to_reconstruction_review",
)


REQUIRED_COMPONENTS: Final = (
    "sharpness",
    "pixel_exposure",
    "object_surface_texture",
    "coverage",
    "metadata_consistency",
)
_CORE_STATUSES = frozenset({"pass", "warning", "failed", "unavailable"})
_COMPONENT_STATUSES = {
    "metadata_consistency": frozenset({"pass", "failed", "unavailable"}),
    "object_surface_texture": _CORE_STATUSES | {"not_requested"},
}
_RECAPTURE_DECISIONS = frozenset(
    {"no_recapture_indicated", "targeted_recapture", "full_rescan", "unavailable"}
)


class RescanDecisionError(ValueError):
    """Raised when the inputs are not the expected QA evidence contracts."""


def _digest(value: Mapping[str, object]) -> str:
    try:
        data = json.dumps(dict(value), sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as error:
        raise RescanDecisionError("evidence payload is not canonical JSON") from error
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _status(components: Mapping[str, object], name: str) -> str | None:
    component = components.get(name)
    if not isinstance(component, Mapping):
        return None
    status = component.get("status")
    return status if isinstance(status, str) else None


def decide_rescan(
    qa_report: Mapping[str, object], recapture_report: Mapping[str, object] | None = None
) -> dict[str, object]:
    """Return an advisory, ordered action list derived only from the supplied evidence."""
    if (
        not isinstance(qa_report, Mapping)
        or qa_report.get("schema") != "packlab.pre-reconstruction-qa.v1"
        or qa_report.get("authority") != "non_authoritative_capture_qa"
        or not isinstance(qa_report.get("components"), Mapping)
        or not isinstance(qa_report.get("photos"), list)
    ):
        raise RescanDecisionError("a pre-reconstruction QA report payload is required")
    if recapture_report is not None and (
        not isinstance(recapture_report, Mapping)
        or recapture_report.get("contract") != "packlab.recapture-sector-suggestions.v1"
    ):
        raise RescanDecisionError("recapture report must be a recapture-sector payload")
    source_evidence = {
        "qa_report_sha256": _digest(qa_report),
        "recapture_report_sha256": (
            _digest(recapture_report) if recapture_report is not None else None
        ),
    }
    components = qa_report["components"]
    assert isinstance(components, Mapping)
    raw_photos = qa_report["photos"]
    assert isinstance(raw_photos, list)
    photos = [item for item in raw_photos if isinstance(item, Mapping)]
    triggered: dict[str, dict[str, object]] = {}

    def add(action: str, reason_code: str, **evidence: object) -> None:
        entry = triggered.setdefault(action, {"action": action, "reason_codes": []})
        reasons = entry["reason_codes"]
        assert isinstance(reasons, list)
        reasons.append(reason_code)
        entry.update(evidence)

    statuses = {name: _status(components, name) for name in REQUIRED_COMPONENTS}
    metadata = statuses["metadata_consistency"]
    if metadata == "failed":
        add("stop_reimport_source", "photo_metadata_inconsistent")
    elif metadata == "unavailable":
        add("stop_reimport_source", "photo_metadata_missing")

    coverage = components.get("coverage")
    coverage_mode = (
        coverage["evidence"].get("mode")
        if isinstance(coverage, Mapping) and isinstance(coverage.get("evidence"), Mapping)
        else None
    )
    if statuses["coverage"] == "warning" and metadata not in {"failed", "unavailable"}:
        if coverage_mode == "guided_orbit":
            add("full_rescan", "capture_view_count_below_declared_target")
        else:
            # One PackScan carries one turntable frame; frame coverage is a session-level check.
            add("manual_review_insufficient_evidence", "coverage_needs_session_level_check")
    recapture_decision = recapture_report.get("decision") if recapture_report is not None else None
    if recapture_decision == "full_rescan":
        add("full_rescan", "recapture_report_requires_full_rescan")

    texture = components.get("object_surface_texture")
    evidence = texture.get("evidence") if isinstance(texture, Mapping) else None
    if isinstance(evidence, Mapping):
        low = evidence.get("low_texture_image_count")
        assessed = evidence.get("assessed_image_count")
        if (
            not isinstance(low, int)
            or not isinstance(assessed, int)
            or isinstance(low, bool)
            or isinstance(assessed, bool)
            or not 0 <= low <= assessed
        ):
            add("manual_review_insufficient_evidence", "texture_counts_malformed")
        elif low and low / assessed >= LOW_TEXTURE_VIEW_FRACTION:
            add(
                "surface_treatment_review",
                "majority_of_views_low_object_texture",
                low_texture_view_fraction=low / assessed,
            )
        elif low:
            add("manual_review_insufficient_evidence", "some_views_low_object_texture")

    if recapture_decision == "targeted_recapture":
        suggestions = recapture_report.get("suggestions") if recapture_report else None
        sectors = [
            item["sector_id"]
            for item in (suggestions if isinstance(suggestions, list) else [])
            if isinstance(item, Mapping) and isinstance(item.get("sector_id"), str)
        ]
        if sectors:
            add("targeted_recapture", "unobserved_view_sectors", sector_ids=sectors)
        else:
            add("manual_review_insufficient_evidence", "targeted_recapture_without_sectors")

    flagged = sorted(
        str(photo.get("image_path"))
        for photo in photos
        if any(
            isinstance(photo.get(check), Mapping) and photo[check].get("status") == "warning"
            for check in ("sharpness", "pixel_exposure")
        )
    )
    if flagged:
        add("retake_flagged_photos", "sharpness_or_exposure_warning", image_paths=flagged)

    unavailable = sorted(name for name, status in statuses.items() if status == "unavailable")
    if unavailable:
        add(
            "manual_review_insufficient_evidence",
            "qa_component_unavailable",
            unavailable_components=unavailable,
        )
    unknown = sorted(
        name
        for name, status in statuses.items()
        if status not in _COMPONENT_STATUSES.get(name, _CORE_STATUSES)
    )
    if unknown:
        add(
            "manual_review_insufficient_evidence",
            "qa_component_missing_or_status_unknown",
            unknown_components=unknown,
        )
    if recapture_report is None or recapture_decision not in _RECAPTURE_DECISIONS:
        add("manual_review_insufficient_evidence", "recapture_evidence_missing_or_unknown")
    elif recapture_decision == "unavailable":
        add("manual_review_insufficient_evidence", "recapture_evidence_unavailable")

    # "Proceed" needs positive evidence, not merely the absence of a triggered rule.
    overall = qa_report.get("overall")
    conclusive = (
        isinstance(overall, Mapping)
        and overall.get("status") == "no_automated_concern"
        and recapture_decision == "no_recapture_indicated"
        and bool(photos)
        and all(
            status == "pass" or (name == "object_surface_texture" and status == "not_requested")
            for name, status in statuses.items()
        )
    )
    if not triggered:
        if conclusive:
            add("proceed_to_reconstruction_review", "no_automated_concern")
        else:
            add("manual_review_insufficient_evidence", "evidence_not_conclusive")

    ordered = [triggered[action] for action in ACTIONS if action in triggered]
    return {
        "contract": RESCAN_DECISION_CONTRACT,
        "authority": "advisory_only_operator_confirms_every_action",
        "claim_limit": "no_capture_acceptance_reconstruction_quality_or_physical_accuracy",
        "primary_action": ordered[0]["action"],
        "actions": ordered,
        "source_evidence": source_evidence,
        "policy": {"low_texture_view_fraction": LOW_TEXTURE_VIEW_FRACTION},
    }
