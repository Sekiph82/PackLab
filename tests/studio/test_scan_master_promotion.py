from __future__ import annotations

import json
from types import SimpleNamespace

import pytest
from PySide6.QtWidgets import QApplication

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_studio.navigation import Route, ScanMasterEditorView
from packlab_studio.project import ProjectError, ProjectManager, RevisionConflict
from packlab_studio.scan_master_promotion import (
    ScanMasterPromotionAction,
    ScanMasterPromotionRequest,
    load_scan_master_revision,
)
from packlab_studio.shell import StudioMainWindow

MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _revision(project_id: str) -> ScanMasterRevision:
    digest = "a" * 64
    revision_id = f"scan-master:{digest}"
    manifest = {
        "scan_master_revision_id": revision_id,
        "project_id": project_id,
        "authority_class": "SCAN_MASTER",
        "raw_capture_sha256": "b" * 64,
        "reconstruction_revision_id": "reconstruction-r1",
        "parent_object_geometry_revision_id": "object-r1",
        "output_geometry_sha256": mesh_sha256(MESH),
        "scale_state": "METRIC_UNVERIFIED",
        "scale_provenance_id": "scale-provenance:r1",
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "mold_use_authorized": False,
        "promotion_actor": "operator-1",
        "promotion_reason": "Reviewed captured cleanup lineage.",
        "hole_report": {"parent_revision_id": "cleanup-r1"},
    }
    return ScanMasterRevision(revision_id, project_id, MESH, manifest)


def _request(project_id: str) -> ScanMasterPromotionRequest:
    return ScanMasterPromotionRequest(
        lineage=SimpleNamespace(project_id=project_id),
        parent_revision_id="aligned-r1",
        parent_mesh=MESH,
        cleanup_operations=(),
        final_mesh=MESH,
        hole_report=object(),
        promoted_at_utc="2026-10-03T10:00:00Z",
        actor_id="operator-1",
        reason="Reviewed captured cleanup lineage.",
        known_limitations=("test fixture",),
        coverage_gaps=("test fixture",),
    )


def test_action_delegates_to_core_persists_revision_and_reopens_with_deferred_state(
    tmp_path, monkeypatch
) -> None:
    import packlab_studio.scan_master_promotion as promotion_module

    manager = ProjectManager()
    project = manager.new_project(tmp_path / "project", "Project")
    result = _revision(project.project_id)
    calls: list[dict[str, object]] = []

    def core_promotion(**values):
        calls.append(values)
        return result

    monkeypatch.setattr(promotion_module, "promote_scan_master", core_promotion)
    promoted = ScanMasterPromotionAction(manager).promote(
        _request(project.project_id), expected_project_revision=0
    )
    assert promoted is result
    assert calls[0]["promotion_reason"] == "Reviewed captured cleanup lineage."
    state = json.loads((tmp_path / "project" / "working" / "state.json").read_text())
    assert state["active_scan_master_revision_id"] == result.revision_id
    assert state["scan_master_revisions"][0]["physical_accuracy_validation_status"] == (
        "DEFERRED_OWNER_VALIDATION"
    )
    assert state["scan_master_revisions"][0]["scale_state"] == "METRIC_UNVERIFIED"
    assert state["scan_master_revisions"][0]["mold_use_authorized"] is False
    assert state["scan_master_selection_events"][0]["reason"] == (
        "Reviewed captured cleanup lineage."
    )

    manager.close()
    reopened = ProjectManager()
    reopened.open_project(tmp_path / "project")
    loaded = load_scan_master_revision(reopened, result.revision_id)
    assert loaded.manifest["promotion_reason"] == "Reviewed captured cleanup lineage."
    assert loaded.manifest["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert loaded.manifest["mold_use_authorized"] is False
    assert mesh_sha256(loaded.mesh) == mesh_sha256(MESH)


def test_action_rejects_stale_project_revision_before_domain_call(tmp_path, monkeypatch) -> None:
    import packlab_studio.scan_master_promotion as promotion_module

    manager = ProjectManager()
    project = manager.new_project(tmp_path / "project", "Project")
    manager.commit_edit({"changed": True}, expected_revision=0)
    monkeypatch.setattr(
        promotion_module,
        "promote_scan_master",
        lambda **_values: pytest.fail("stale state reached the core promotion call"),
    )
    with pytest.raises(RevisionConflict):
        ScanMasterPromotionAction(manager).promote(
            _request(project.project_id), expected_project_revision=0
        )


def test_reopen_rejects_scan_master_artifact_tampering(tmp_path, monkeypatch) -> None:
    import packlab_studio.scan_master_promotion as promotion_module

    manager = ProjectManager()
    project = manager.new_project(tmp_path / "project", "Project")
    result = _revision(project.project_id)
    monkeypatch.setattr(promotion_module, "promote_scan_master", lambda **_values: result)
    ScanMasterPromotionAction(manager).promote(
        _request(project.project_id), expected_project_revision=0
    )
    manager.close()
    reopened = ProjectManager()
    reopened.open_project(tmp_path / "project")
    state = json.loads((tmp_path / "project" / "working" / "state.json").read_text())
    artifact = (
        tmp_path / "project" / "derived" / state["scan_master_revisions"][0]["artifact_directory"]
    )
    (artifact / "mesh.json").write_text("{}", encoding="utf-8")
    with pytest.raises(ProjectError, match="mesh file digest mismatch"):
        load_scan_master_revision(reopened, result.revision_id)


def test_editor_promote_action_delegates_request_and_shows_deferred_authority(
    tmp_path, monkeypatch
) -> None:
    import packlab_studio.scan_master_promotion as promotion_module
    from packlab_studio.app import create_application

    app = create_application(["packlab-scan-master-test"])
    project_holder: dict[str, object] = {}
    provided: list[tuple[str, str]] = []

    def provider(actor: str, reason: str):
        provided.append((actor, reason))
        project = project_holder["window"].project_manager.current
        return _request(project.project_id)

    window = StudioMainWindow(scan_master_request_provider=provider)
    project_holder["window"] = window
    project = window.new_project(tmp_path / "project", "Project")
    result = _revision(project.project_id)
    monkeypatch.setattr(promotion_module, "promote_scan_master", lambda **_values: result)
    editor = window.route_stack.views[Route.EDITOR]
    assert isinstance(editor, ScanMasterEditorView)
    editor.actor_input.setText("operator-7")
    editor.reason_input.setText("Reviewed full captured cleanup chain.")
    editor.promote_button.click()
    app.processEvents()
    assert provided == [("operator-7", "Reviewed full captured cleanup chain.")]
    assert "DEFERRED_OWNER_VALIDATION" in editor.authority_status.text()
    assert "mold_use_authorized=false" in editor.authority_status.text()
    assert window.project_manager.current is not None
    assert window.project_manager.current.revision == 1
    window.close()


def test_editor_requires_actor_and_reason_and_displays_deferred_default() -> None:
    app = QApplication.instance()
    if app is None:
        from packlab_studio.app import create_application

        app = create_application(["packlab-scan-master-view-test"])
    editor = ScanMasterEditorView()
    editor.promote_button.click()
    assert "requires an actor and reason" in editor.status.text()
    assert "DEFERRED_OWNER_VALIDATION" in editor.authority_status.text()
    assert "mold_use_authorized=false" in editor.authority_status.text()
