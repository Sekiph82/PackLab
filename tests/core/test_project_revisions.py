from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.project_revisions import (
    ImmutableCaptureReference,
    ProjectRevisionError,
    ProjectRevisionKind,
    ProjectRevisionRecord,
    ProjectRevisionRegistry,
)
from packlab_core.reconstruction import ScaleState

PROJECT = "f3343d5e-bf9c-44ab-b519-bbdfca5401a0"
PROVENANCE = "scale-provenance-project-revision-r1"
RAW = ImmutableCaptureReference("raw-capture-r1", hashlib.sha256(b"raw capture").hexdigest())


def _record(
    revision_id: str,
    kind: ProjectRevisionKind,
    parents: tuple[str, ...] = (),
    *,
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    provenance: str | None = PROVENANCE,
) -> ProjectRevisionRecord:
    authority = {
        ProjectRevisionKind.RECONSTRUCTION: "RECONSTRUCTION_OBSERVATION",
        ProjectRevisionKind.OBJECT_GEOMETRY: "OBJECT_CAPTURE_GEOMETRY",
        ProjectRevisionKind.M10_CLEANUP: "M10_CLEANUP",
        ProjectRevisionKind.SCAN_MASTER: "SCAN_MASTER",
    }[kind]
    return ProjectRevisionRecord(
        revision_id,
        kind,
        hashlib.sha256(revision_id.encode("ascii")).hexdigest(),
        parents,
        scale_state,
        provenance,
        authority,
        physical_accuracy_validation_status=(
            "DEFERRED_OWNER_VALIDATION" if kind is ProjectRevisionKind.SCAN_MASTER else None
        ),
        mold_use_authorized=False,
        source_capture_references=(RAW,) if kind is ProjectRevisionKind.RECONSTRUCTION else (),
    )


def _append_chain(
    registry: ProjectRevisionRegistry, suffix: str
) -> tuple[ProjectRevisionRegistry, tuple[ProjectRevisionRecord, ...]]:
    records = (
        _record(f"reconstruction-{suffix}", ProjectRevisionKind.RECONSTRUCTION),
        _record(
            f"object-geometry-{suffix}",
            ProjectRevisionKind.OBJECT_GEOMETRY,
            (f"reconstruction-{suffix}",),
        ),
        _record(
            f"cleanup-{suffix}",
            ProjectRevisionKind.M10_CLEANUP,
            (f"object-geometry-{suffix}",),
        ),
        _record(
            f"scan-master-{suffix}",
            ProjectRevisionKind.SCAN_MASTER,
            (f"cleanup-{suffix}",),
        ),
    )
    for record in records:
        registry = registry.append_revision(record, expected_state_revision=registry.state_revision)
    return registry, records


def test_append_reopen_and_switch_active_revision_preserves_history() -> None:
    registry, first_chain = _append_chain(ProjectRevisionRegistry.create(PROJECT), "r1")
    registry, second_chain = _append_chain(registry, "r2")
    registry = registry.select_active(
        ProjectRevisionKind.SCAN_MASTER,
        second_chain[-1].revision_id,
        expected_state_revision=registry.state_revision,
    )

    reopened = ProjectRevisionRegistry.deserialize(registry.serialize())
    assert reopened == registry
    assert reopened.active_revision(ProjectRevisionKind.SCAN_MASTER) == second_chain[-1]
    assert reopened.revisions == (*first_chain, *second_chain)
    assert reopened.selection_events[-1].selected_revision_id == second_chain[-1].revision_id
    with pytest.raises(ProjectRevisionError, match="active_revision_pointer_history_mismatch"):
        replace(
            reopened,
            active_revision_ids=((ProjectRevisionKind.SCAN_MASTER, first_chain[-1].revision_id),),
        )

    switched = reopened.select_active(
        ProjectRevisionKind.SCAN_MASTER,
        first_chain[-1].revision_id,
        expected_state_revision=reopened.state_revision,
    )
    assert switched.active_revision(ProjectRevisionKind.SCAN_MASTER) == first_chain[-1]
    assert switched.revisions == reopened.revisions
    assert switched.revisions[-1].parent_revision_ids == second_chain[-1].parent_revision_ids
    assert switched.selection_events[-1].previous_revision_id == second_chain[-1].revision_id


def test_duplicate_missing_and_wrong_kind_revisions_are_rejected() -> None:
    registry = ProjectRevisionRegistry.create(PROJECT)
    reconstruction = _record("reconstruction-r1", ProjectRevisionKind.RECONSTRUCTION)
    registry = registry.append_revision(reconstruction, expected_state_revision=0)
    with pytest.raises(ProjectRevisionError, match="duplicate_project_revision_id"):
        registry.append_revision(reconstruction, expected_state_revision=1)
    with pytest.raises(ProjectRevisionError, match="project_revision_parent_missing"):
        registry.append_revision(
            _record("object-geometry-r1", ProjectRevisionKind.OBJECT_GEOMETRY, ("missing",)),
            expected_state_revision=1,
        )
    with pytest.raises(ProjectRevisionError, match="project_revision_parent_kind_invalid"):
        registry.append_revision(
            _record(
                "cleanup-r1",
                ProjectRevisionKind.M10_CLEANUP,
                ("reconstruction-r1",),
            ),
            expected_state_revision=1,
        )
    with pytest.raises(ProjectRevisionError, match="project_revision_missing"):
        registry.select_active(
            ProjectRevisionKind.SCAN_MASTER,
            "scan-master-missing",
            expected_state_revision=1,
        )
    with pytest.raises(ProjectRevisionError, match="selected_project_revision_kind_mismatch"):
        registry.select_active(
            ProjectRevisionKind.SCAN_MASTER,
            "reconstruction-r1",
            expected_state_revision=1,
        )


def test_optimistic_concurrency_rejects_stale_append_and_selection() -> None:
    base = ProjectRevisionRegistry.create(PROJECT)
    reconstruction = _record("reconstruction-r1", ProjectRevisionKind.RECONSTRUCTION)
    first_writer = base.append_revision(reconstruction, expected_state_revision=0)
    concurrent_writer = base.append_revision(reconstruction, expected_state_revision=0)
    object_revision = _record(
        "object-geometry-r1", ProjectRevisionKind.OBJECT_GEOMETRY, ("reconstruction-r1",)
    )
    updated = first_writer.append_revision(object_revision, expected_state_revision=1)
    with pytest.raises(ProjectRevisionError, match="project_revision_concurrency_conflict"):
        updated.append_revision(
            _record("cleanup-r1", ProjectRevisionKind.M10_CLEANUP, ("object-geometry-r1",)),
            expected_state_revision=1,
        )
    with pytest.raises(ProjectRevisionError, match="project_revision_concurrency_conflict"):
        concurrent_writer.select_active(
            ProjectRevisionKind.RECONSTRUCTION,
            "reconstruction-r1",
            expected_state_revision=0,
        )


def test_scan_master_deferred_state_raw_ancestry_and_scale_are_persisted() -> None:
    registry, records = _append_chain(ProjectRevisionRegistry.create(PROJECT), "r1")
    scan_master = records[-1]
    assert scan_master.source_capture_references == ()
    assert records[0].source_capture_references == (RAW,)
    assert scan_master.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert scan_master.scale_state is ScaleState.METRIC_UNVERIFIED
    assert scan_master.scale_provenance_id == PROVENANCE
    assert scan_master.mold_use_authorized is False
    reopened = ProjectRevisionRegistry.deserialize(registry.serialize())
    assert reopened.get_revision(scan_master.revision_id) == scan_master
    with pytest.raises(
        ProjectRevisionError, match="scan_master_scale_and_deferred_authority_required"
    ):
        replace(scan_master, scale_state=ScaleState.METRIC_VERIFIED)
    with pytest.raises(ProjectRevisionError, match="generated_geometry_forbidden"):
        replace(records[1], generated=True)


def test_registry_serialization_detects_corruption_and_duplicate_json_keys() -> None:
    registry, _ = _append_chain(ProjectRevisionRegistry.create(PROJECT), "r1")
    payload = registry.serialize()
    corrupted = payload.replace(b"scan-master-r1", b"scan-master-x1", 1)
    with pytest.raises(ProjectRevisionError, match="serialized_registry_digest_mismatch"):
        ProjectRevisionRegistry.deserialize(corrupted)
    with pytest.raises(ProjectRevisionError, match="serialized_registry_duplicate_json_key"):
        ProjectRevisionRegistry.deserialize('{"body":{},"body":{},"content_sha256":"x"}')
