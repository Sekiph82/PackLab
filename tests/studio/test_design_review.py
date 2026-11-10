from __future__ import annotations

import hashlib

import pytest
from PySide6.QtCore import QSize

from packlab_core.design_model import (
    PackageFamily,
    create_design_model_revision,
    create_standalone_design_model_revision,
)
from packlab_core.design_model_binding import (
    StandaloneDesignGeometrySourceKind,
    bind_design_model_parent,
    create_standalone_design_geometry_root,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256
from packlab_studio.app import create_application
from packlab_studio.design_review import (
    DesignReviewError,
    DesignReviewMode,
    ScanDesignReviewBinding,
    ScanDesignReviewWidget,
    preview_geometry_sha256,
)
from packlab_studio.viewport import MeshGeometry, QtRasterViewportAdapter

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
NOW = "2026-10-03T12:00:00Z"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)
PREVIEW = MeshGeometry(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


class _CameraRecordingAdapter(QtRasterViewportAdapter):
    def __init__(self) -> None:
        self.rendered_cameras = []

    def render(self, scene, state, size=QSize(960, 640)):
        self.rendered_cameras.append(state.camera)
        return super().render(scene, state, size)


def _scan() -> ScanMasterRevision:
    digest = hashlib.sha256(b"design-review-scan").hexdigest()
    revision_id = f"scan-master:{digest}"
    return ScanMasterRevision(
        revision_id,
        PROJECT,
        MESH,
        {
            "scan_master_revision_id": revision_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction:review-fixture",
            "scale_state": ScaleState.METRIC_UNVERIFIED.value,
            "scale_provenance_id": "scale-provenance:review-fixture",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )


def _model(scan: ScanMasterRevision):
    binding = bind_design_model_parent(
        scan,
        actor_id="operator-1",
        reason="Review fixture exact source binding.",
        created_at_utc=NOW,
    )
    return create_design_model_revision(
        binding,
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="Review fixture model.",
        created_at_utc=NOW,
    )


def _standalone_model(project_id: str = PROJECT):
    root = create_standalone_design_geometry_root(
        project_id=project_id,
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="nominal-input:review-fixture",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="unit-choice:mm-unverified",
        actor_id="operator-1",
        reason="Standalone review fixture.",
        created_at_utc=NOW,
    )
    return create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="Standalone review fixture model.",
        created_at_utc=NOW,
    )


def test_binding_pins_exact_revision_ids_digests_and_non_authoritative_status() -> None:
    scan = _scan()
    model = _model(scan)
    binding = ScanDesignReviewBinding.create(scan, model, PREVIEW)

    metadata = binding.metadata()

    assert binding.is_exactly_scan_fitted is True
    assert metadata["scan_master_revision_id"] == scan.revision_id
    assert metadata["scan_master_geometry_sha256"] == mesh_sha256(MESH)
    assert metadata["design_model_revision_id"] == model.revision_id
    assert metadata["design_model_preview_geometry_sha256"] == preview_geometry_sha256(PREVIEW)
    assert metadata["authority"] == "REVIEW_ONLY_NON_AUTHORITATIVE"


def test_stale_preview_digest_and_cross_project_revisions_are_rejected() -> None:
    scan = _scan()
    model = _model(scan)
    with pytest.raises(DesignReviewError, match="design_preview_digest_mismatch"):
        ScanDesignReviewBinding(scan, model, PREVIEW, "0" * 64)

    mismatched = _standalone_model("other-project")
    with pytest.raises(DesignReviewError, match="review_project_mismatch"):
        ScanDesignReviewBinding.create(scan, mismatched, PREVIEW)


def test_ghosted_overlay_requires_exact_scan_master_ancestry() -> None:
    create_application(["packlab-design-review-test"])
    scan = _scan()
    widget = ScanDesignReviewWidget(
        ScanDesignReviewBinding.create(scan, _standalone_model(), PREVIEW)
    )
    with pytest.raises(DesignReviewError, match="ghost_overlay_requires_exact_scan_master_parent"):
        widget.set_mode(DesignReviewMode.GHOSTED)

    widget.set_mode(DesignReviewMode.SIDE_BY_SIDE)
    assert widget.mode is DesignReviewMode.SIDE_BY_SIDE
    assert widget.sizeHint().isValid()


def test_exact_parent_enables_ghost_mode_and_renders_distinct_overlay() -> None:
    create_application(["packlab-design-review-linked-test"])
    scan = _scan()
    preview = MeshGeometry(
        ((10.0, 0.0, 0.0), (12.0, 0.0, 0.0), (10.0, 2.0, 0.0)),
        ((0, 1, 2),),
    )
    adapter = _CameraRecordingAdapter()
    widget = ScanDesignReviewWidget(
        ScanDesignReviewBinding.create(scan, _model(scan), preview), adapter=adapter
    )
    widget.resize(QSize(560, 240))
    adapter.rendered_cameras.clear()
    widget.set_mode(DesignReviewMode.GHOSTED)
    widget.show()
    widget.repaint()

    assert widget.mode is DesignReviewMode.GHOSTED
    assert "REVIEW ONLY" in widget.status_label.text()
    assert widget.overlay_label.isVisible()
    assert not widget.scan_label.isVisible()
    assert len(adapter.rendered_cameras) >= 2
    assert all(camera == adapter.rendered_cameras[0] for camera in adapter.rendered_cameras)
    assert mesh_sha256(scan.mesh) in widget.overlay_caption.text()
    assert widget.binding.design_preview_sha256 in widget.overlay_caption.text()
    assert widget.binding.design_preview_sha256 in widget.status_label.text()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("authority_class", "DESIGN_MODEL"),
        ("mold_use_authorized", True),
        ("physical_accuracy_validation_status", "ACCEPTED"),
        ("output_geometry_sha256", "0" * 64),
    ],
)
def test_scan_master_manifest_authority_is_enforced(key: str, value: object) -> None:
    # Review P2-3: the authority half of the manifest check had no test.
    scan = _scan()
    forged = ScanMasterRevision(scan.revision_id, PROJECT, MESH, {**scan.manifest, key: value})
    with pytest.raises(
        DesignReviewError, match="scan_master_manifest_identity_or_authority_invalid"
    ):
        ScanDesignReviewBinding.create(forged, _model(scan), PREVIEW)


def test_matching_revision_id_with_a_different_geometry_digest_is_not_exactly_fitted() -> None:
    import copy

    scan = _scan()
    stale = copy.copy(_model(scan))
    # Test-only forgery of a model whose revision id matches but whose digest does not.
    object.__setattr__(stale, "scan_master_geometry_sha256", "0" * 64)
    assert stale.fitted_to_scan_master_revision_id == scan.revision_id
    binding = ScanDesignReviewBinding.create(scan, stale, PREVIEW)
    assert binding.is_exactly_scan_fitted is False
    assert binding.metadata()["relationship"] == "UNLINKED_OR_STANDALONE"


def test_combo_box_cannot_enable_ghosting_for_an_unlinked_model() -> None:
    # The real user path (combo box) must apply the same guard as set_mode.
    create_application(["packlab-design-review-combo-test"])
    widget = ScanDesignReviewWidget(
        ScanDesignReviewBinding.create(_scan(), _standalone_model(), PREVIEW)
    )
    widget.mode_picker.setCurrentIndex(1)
    assert widget.mode is DesignReviewMode.SIDE_BY_SIDE
    assert widget.mode_picker.currentIndex() == 0
    assert widget.status_label.text().startswith("REVIEW ONLY")
    assert "Ghosting unavailable" in widget.status_label.text()
    assert "unverified" in widget.design_caption.text()


def test_ghost_composite_matches_the_reference_mask_and_is_fast() -> None:
    import time

    from PySide6.QtGui import QColor, QImage

    from packlab_studio.design_review import _BACKGROUND, _ghost_composite

    create_application(["packlab-design-review-composite-test"])
    scan = QImage(1600, 900, QImage.Format.Format_ARGB32)
    scan.fill(_BACKGROUND)
    design = QImage(scan)
    for x in range(100, 300):
        scan.setPixelColor(x, 50, QColor("#ffffff"))
        design.setPixelColor(x, 60, QColor("#808080"))
    started = time.perf_counter()
    result = _ghost_composite(scan, design)
    elapsed = time.perf_counter() - started
    assert result.pixelColor(150, 50) != _BACKGROUND
    assert result.pixelColor(150, 60) != _BACKGROUND
    assert result.pixelColor(150, 55) == _BACKGROUND
    assert result.pixelColor(150, 50) != result.pixelColor(150, 60)
    assert elapsed < 0.5, elapsed
