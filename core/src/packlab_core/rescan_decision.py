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


class RescanDecisionError(ValueError):
    """Raised when the inputs are not the expected QA evidence contracts."""


def _digest(value: Mapping[str, object]) -> str:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
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

    if _status(components, "metadata_consistency") == "failed":
        add("stop_reimport_source", "photo_metadata_inconsistent")
    if _status(components, "coverage") == "warning":
        add("full_rescan", "capture_coverage_below_declared_target")
    recapture_decision = recapture_report.get("decision") if recapture_report is not None else None
    if recapture_decision == "full_rescan":
        add("full_rescan", "recapture_report_requires_full_rescan")

    texture = components.get("object_surface_texture")
    evidence = texture.get("evidence") if isinstance(texture, Mapping) else None
    if isinstance(evidence, Mapping):
        low = evidence.get("low_texture_image_count")
        assessed = evidence.get("assessed_image_count")
        if isinstance(low, int) and isinstance(assessed, int) and assessed > 0 and low > 0:
            if low / assessed >= LOW_TEXTURE_VIEW_FRACTION:
                add(
                    "surface_treatment_review",
                    "majority_of_views_low_object_texture",
                    low_texture_view_fraction=low / assessed,
                )

    if recapture_decision == "targeted_recapture":
        suggestions = recapture_report.get("suggestions") if recapture_report else None
        sectors = [
            item["sector_id"]
            for item in (suggestions if isinstance(suggestions, list) else [])
            if isinstance(item, Mapping) and isinstance(item.get("sector_id"), str)
        ]
        add("targeted_recapture", "unobserved_view_sectors", sector_ids=sectors)

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

    unavailable = sorted(
        name
        for name in components
        if isinstance(name, str) and _status(components, name) == "unavailable"
    )
    if unavailable:
        add(
            "manual_review_insufficient_evidence",
            "qa_component_unavailable",
            unavailable_components=unavailable,
        )
    if recapture_report is None or recapture_decision == "unavailable":
        add("manual_review_insufficient_evidence", "recapture_evidence_unavailable")
    if not triggered:
        add("proceed_to_reconstruction_review", "no_automated_concern")

    ordered = [triggered[action] for action in ACTIONS if action in triggered]
    return {
        "contract": RESCAN_DECISION_CONTRACT,
        "authority": "advisory_only_operator_confirms_every_action",
        "claim_limit": "no_capture_acceptance_reconstruction_quality_or_physical_accuracy",
        "primary_action": ordered[0]["action"],
        "actions": ordered,
        "source_evidence": {
            "qa_report_sha256": _digest(qa_report),
            "recapture_report_sha256": (
                _digest(recapture_report) if recapture_report is not None else None
            ),
        },
        "policy": {"low_texture_view_fraction": LOW_TEXTURE_VIEW_FRACTION},
    }
