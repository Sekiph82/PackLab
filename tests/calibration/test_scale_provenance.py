from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from packlab_core.calibration import (
    AssociatedMarkerObservation,
    PhysicalMarkerReference,
    ReconstructedMarkerGeometry,
    ReconstructionScaleObservation,
    estimate_reconstruction_scale,
)
from packlab_core.calibration.scale_provenance import (
    ScalePromotionEvidence,
    ScaleProvenanceError,
    VerifiedPhysicalReference,
    append_scale_provenance_revision,
    create_scale_provenance,
    promote_scale_provenance,
    serialize_scale_provenance,
)
from packlab_core.coordinate_frame import coordinate_unit_for_scale_state
from packlab_core.reconstruction import ScaleState
from packlab_studio.project import ProjectError, ProjectManager

RECONSTRUCTION = "reconstruction-r1"
CAMERA = "camera-solution-r1"
CREATED = "2026-10-02T10:00:00Z"


def _sample(marker_id: int, *, side_units: float = 100.0) -> ReconstructionScaleObservation:
    source_id = f"synthetic-source-{marker_id}"
    digest = hashlib.sha256(source_id.encode()).hexdigest()
    observation = AssociatedMarkerObservation(
        marker_id,
        ((0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)),
        {"quality_label": "synthetic_geometry", "quality_score": 1.0},
        {"generator": "synthetic_test_fixture_v1"},
        source_id,
        digest,
        640,
        480,
        f"camera-{marker_id}",
        CAMERA,
    )
    reference = PhysicalMarkerReference(
        marker_id,
        f"synthetic-reference-{marker_id}",
        hashlib.sha256(f"reference-{marker_id}".encode()).hexdigest(),
        40.0,
        "mm",
        0.1,
        "synthetic_test_fixture",
    )
    geometry = ReconstructedMarkerGeometry(
        observation,
        RECONSTRUCTION,
        "reconstruction_units",
        (
            (0.0, 0.0, 5.0),
            (side_units, 0.0, 5.0),
            (side_units, side_units, 5.0),
            (0.0, side_units, 5.0),
        ),
        0.05,
    )
    return ReconstructionScaleObservation(reference, geometry)


def _estimate(samples=None):
    values = (_sample(1), _sample(2)) if samples is None else samples
    return estimate_reconstruction_scale(
        values,
        reconstruction_revision=RECONSTRUCTION,
        camera_solution_revision=CAMERA,
    )


def _provenance(samples=None, *, created_at=CREATED):
    values = (_sample(1), _sample(2)) if samples is None else samples
    return create_scale_provenance(
        _estimate(values),
        values,
        reconstruction_revision=RECONSTRUCTION,
        camera_solution_revision=CAMERA,
        created_at_utc=created_at,
        actor_id="test-actor",
        process_id="test-scale-run",
    )


def test_relative_state_cannot_be_labeled_millimetres() -> None:
    assert coordinate_unit_for_scale_state(ScaleState.RELATIVE) == "reconstruction_units"
    assert coordinate_unit_for_scale_state(ScaleState.METRIC_UNVERIFIED) == "mm_unverified"
    assert coordinate_unit_for_scale_state(ScaleState.METRIC_VERIFIED) == "mm"


def test_rejected_scale_stays_relative_and_has_no_millimetre_factor() -> None:
    provenance = _provenance((_sample(1),))
    assert provenance.scale_state is ScaleState.RELATIVE
    assert provenance.estimated_scale_factor_mm_per_reconstruction_unit is None
    assert provenance.uncertainty is None
    assert coordinate_unit_for_scale_state(provenance.scale_state) == "reconstruction_units"
    with pytest.raises(ScaleProvenanceError, match="requires_unverified_estimate"):
        promote_scale_provenance(
            provenance,
            ScalePromotionEvidence(
                "synthetic_test_fixture",
                "synthetic_test_fixture",
                "synthetic-record",
                hashlib.sha256(b"synthetic").hexdigest(),
                "UNRECORDED",
                "2026-10-02T10:00:00Z",
                "test-operator",
                "synthetic ruler",
                False,
                (
                    VerifiedPhysicalReference(
                        "synthetic-reference-1",
                        hashlib.sha256(b"reference-1").hexdigest(),
                        1,
                        40.0,
                    ),
                ),
            ),
        )


def test_scale_provenance_persists_all_estimate_inputs_and_is_deterministic() -> None:
    samples = (_sample(1), _sample(2))
    first = _provenance(samples)
    repeated = _provenance(samples)
    record = first.as_dict()
    assert record["scale_state"] == ScaleState.METRIC_UNVERIFIED.value
    assert len(record["calibration_observation_ids"]) == 2
    assert len(record["physical_references"]) == 2
    assert record["estimated_scale_factor"] == pytest.approx(0.4)
    assert record["uncertainty"]["representation"] == (
        "standard_uncertainty_mm_per_reconstruction_unit"
    )
    assert record["actor_process_provenance"] == {
        "actor_id": "test-actor",
        "process_id": "test-scale-run",
    }
    assert first.provenance_id == repeated.provenance_id
    assert serialize_scale_provenance(first) == serialize_scale_provenance(repeated)


def test_rejected_observations_are_retained_but_excluded_from_scale_factor() -> None:
    samples = (_sample(1), _sample(2, side_units=100.2), _sample(3, side_units=70.0))
    provenance = _provenance(samples)
    record = provenance.as_dict()
    assert len(record["calibration_observation_ids"]) == 2
    assert len(record["rejected_observations"]) == 1
    assert record["rejected_observations"][0]["reason"] == "outlier_relative_residual"
    rejected_id = record["rejected_observations"][0]["observation_id"]
    assert rejected_id not in record["calibration_observation_ids"]
    rejected_reference = next(
        item for item in record["physical_references"] if item["observation_id"] == rejected_id
    )
    assert rejected_reference["used_in_estimate"] is False


def test_synthetic_nominal_or_ai_evidence_cannot_promote_scale() -> None:
    provenance = _provenance()
    sample = _sample(1).physical_reference
    evidence = ScalePromotionEvidence(
        "synthetic_test_fixture",
        "synthetic_test_fixture",
        "synthetic-verification-record",
        hashlib.sha256(b"synthetic verification").hexdigest(),
        "ACCEPTED_FOR_CAPTURE",
        "2026-10-02T10:00:00Z",
        "test-operator",
        "synthetic ruler",
        True,
        (
            VerifiedPhysicalReference(
                sample.reference_id,
                sample.reference_digest,
                sample.marker_id,
                sample.side_length,
            ),
        ),
    )
    with pytest.raises(ScaleProvenanceError, match="accepted_owner_physical_evidence"):
        promote_scale_provenance(provenance, evidence)

    ai_evidence = replace(
        evidence,
        evidence_class="generated_visual_reference",
        source_type="AI_VISUAL_REFERENCE",
    )
    with pytest.raises(ScaleProvenanceError, match="accepted_owner_physical_evidence"):
        promote_scale_provenance(provenance, ai_evidence)


def test_promotion_requires_all_used_physical_references_and_complete_record() -> None:
    provenance = _provenance()
    sample = _sample(1).physical_reference
    incomplete = ScalePromotionEvidence(
        "accepted_owner_physical",
        "owner_controlled_physical_record",
        "verification-record-r1",
        hashlib.sha256(b"owner record reference").hexdigest(),
        "UNRECORDED",
        "2026-10-02T10:00:00Z",
        "owner-operator-ref",
        "calibrated-instrument-ref",
        False,
        (
            VerifiedPhysicalReference(
                sample.reference_id,
                sample.reference_digest,
                sample.marker_id,
                sample.side_length,
            ),
        ),
    )
    with pytest.raises(ScaleProvenanceError, match="accepted_owner_physical_evidence"):
        promote_scale_provenance(provenance, incomplete)


def test_parent_reconstruction_change_invalidates_provenance_append() -> None:
    provenance = _provenance()
    with pytest.raises(ScaleProvenanceError, match="stale_reconstruction_parent"):
        append_scale_provenance_revision(
            [], provenance, current_reconstruction_revision="reconstruction-r2"
        )
    history = append_scale_provenance_revision(
        [], provenance, current_reconstruction_revision=RECONSTRUCTION
    )
    assert history[0]["provenance_id"] == provenance.provenance_id
    next_record = _provenance(created_at="2026-10-02T10:01:00Z")
    extended = append_scale_provenance_revision(
        history, next_record, current_reconstruction_revision=RECONSTRUCTION
    )
    assert len(history) == 1
    assert len(extended) == 2


def test_reference_classes_reject_unapproved_sources() -> None:
    reference = _sample(1).physical_reference
    with pytest.raises(ValueError, match="evidence_class_invalid"):
        replace(reference, evidence_class="nominal_svg")


def test_scale_provenance_persists_append_only_across_project_reopen(tmp_path) -> None:
    root = tmp_path / "project"
    manager = ProjectManager()
    manager.new_project(root, "Scale provenance test")
    first = _provenance()
    manager.persist_scale_provenance(
        first,
        current_reconstruction_revision=RECONSTRUCTION,
        expected_revision=0,
    )
    manager.close()

    reopened = ProjectManager()
    reopened.open_project(root)
    second = _provenance(created_at="2026-10-02T10:01:00Z")
    reopened.persist_scale_provenance(
        second,
        current_reconstruction_revision=RECONSTRUCTION,
        expected_revision=1,
    )
    reopened.close()

    state = json.loads((root / "working" / "state.json").read_text(encoding="utf-8"))
    measurement = state["measurement_provenance"]
    history = measurement["scale_provenance_revisions"]
    assert [item["provenance_id"] for item in history] == [
        first.provenance_id,
        second.provenance_id,
    ]
    assert measurement["active_scale_provenance_id"] == second.provenance_id
    assert measurement["scale_state"] == ScaleState.METRIC_UNVERIFIED.value


def test_project_persistence_rejects_stale_scale_parent_without_edit(tmp_path) -> None:
    manager = ProjectManager()
    manager.new_project(tmp_path / "project", "Scale provenance test")
    with pytest.raises(ProjectError, match="stale_reconstruction_parent"):
        manager.persist_scale_provenance(
            _provenance(),
            current_reconstruction_revision="reconstruction-r2",
            expected_revision=0,
        )
    assert manager.metadata is not None and manager.metadata.revision == 0
