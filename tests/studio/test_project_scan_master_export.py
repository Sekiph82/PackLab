from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_core.scan_master_export import ScanMasterTextureAsset
from packlab_studio.project import ProjectError, ProjectManager

MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _revision(project_id: str) -> ScanMasterRevision:
    revision_id = f"scan-master:{hashlib.sha256(b'studio-export').hexdigest()}"
    return ScanMasterRevision(
        revision_id,
        project_id,
        MESH,
        {
            "scan_master_revision_id": revision_id,
            "project_id": project_id,
            "authority_class": "SCAN_MASTER",
            "raw_capture_revision_id": "capture-r1",
            "raw_capture_sha256": "b" * 64,
            "reconstruction_revision_id": "reconstruction-r1",
            "parent_object_geometry_revision_id": "object-r1",
            "scale_provenance_id": "scale-r1",
            "scale_state": "metric-unverified",
            "output_geometry_sha256": mesh_sha256(MESH),
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
            "known_limitations": ["synthetic test revision"],
            "coverage_gaps": [],
            "promotion_actor": "operator-test",
            "promotion_reason": "Fixture for export adapter tests.",
            "hole_report": {"parent_revision_id": "cleanup-r1"},
        },
    )


def test_project_exports_only_active_persisted_scan_master(tmp_path) -> None:
    manager = ProjectManager()
    project_root = tmp_path / "project"
    project = manager.new_project(project_root, "Project")
    revision = _revision(project.project_id)
    manager.persist_scan_master_revision(revision, expected_revision=0)
    with pytest.raises(ProjectError, match="requires the selected project revision"):
        manager.export_selected_scan_master(
            "scan-master:not-active",
            destination_relative_dir="export/scan-master/invalid",
            formats=("ply",),
        )
    result = manager.export_selected_scan_master(
        revision.revision_id,
        destination_relative_dir="export/scan-master/selected",
        formats=("ply", "obj", "glb"),
    )
    manifest = json.loads(result.manifest_path.read_text(encoding="ascii"))
    assert manifest["scan_master_revision_id"] == revision.revision_id
    assert (result.output_directory / "scan-master.glb").is_file()


def test_project_texture_export_requires_matching_original_project_bytes(tmp_path) -> None:
    manager = ProjectManager()
    project_root = tmp_path / "project"
    project = manager.new_project(project_root, "Project")
    revision = _revision(project.project_id)
    manager.persist_scan_master_revision(revision, expected_revision=0)
    texture_path = project_root / "working" / "reconstruction" / "r1" / "original.png"
    texture_path.parent.mkdir(parents=True)
    image = b"\x89PNG\r\n\x1a\noriginal"
    texture_path.write_bytes(image)
    texture = ScanMasterTextureAsset(
        "working/reconstruction/r1/original.png",
        hashlib.sha256(image).hexdigest(),
        image,
        "reconstruction-r1",
    )
    result = manager.export_selected_scan_master(
        revision.revision_id,
        destination_relative_dir="export/scan-master/textured",
        formats=("obj",),
        texture_assets=(texture,),
    )
    assert (result.output_directory / "textures" / "original.png").read_bytes() == image
    forged = ScanMasterTextureAsset(
        "working/reconstruction/r1/original.png",
        hashlib.sha256(b"other").hexdigest(),
        b"other",
        "reconstruction-r1",
    )
    with pytest.raises(ProjectError, match="texture source bytes do not match"):
        manager.export_selected_scan_master(
            revision.revision_id,
            destination_relative_dir="export/scan-master/forged-texture",
            formats=("obj",),
            texture_assets=(forged,),
        )
