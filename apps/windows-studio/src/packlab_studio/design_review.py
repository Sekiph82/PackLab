"""Review-only comparison of immutable captured and design-model revisions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPixmap
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from packlab_core.design_model import DesignModelRevision
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

from .viewport import (
    MeshGeometry,
    QtRasterViewportAdapter,
    SceneModel,
    SceneObject,
    SceneObjectKind,
    ViewportCamera,
    ViewportState,
)

_BACKGROUND = QColor("#101820")


class DesignReviewError(ValueError):
    """Raised when comparison inputs are stale, generated, or malformed."""


class DesignReviewMode(StrEnum):
    SIDE_BY_SIDE = "side-by-side"
    GHOSTED = "ghosted-overlay"


def preview_geometry_sha256(geometry: MeshGeometry) -> str:
    """Digest the supplied display mesh; this is not an engineering authority digest."""

    if not isinstance(geometry, MeshGeometry):
        raise DesignReviewError("design_preview_mesh_required")
    mesh = TriangleMeshData(
        geometry.vertices,
        geometry.triangles,
        vertex_normals=geometry.normals or None,
    )
    return mesh_sha256(mesh)


@dataclass(frozen=True, slots=True)
class ScanDesignReviewBinding:
    """Exact source identity plus a caller-supplied, non-authoritative model preview."""

    scan_master: ScanMasterRevision
    design_model: DesignModelRevision
    design_preview: MeshGeometry
    design_preview_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.scan_master, ScanMasterRevision):
            raise DesignReviewError("scan_master_revision_required")
        if not isinstance(self.design_model, DesignModelRevision):
            raise DesignReviewError("design_model_revision_required")
        if self.scan_master.project_id != self.design_model.project_id:
            raise DesignReviewError("review_project_mismatch")
        scan_digest = mesh_sha256(self.scan_master.mesh)
        manifest = self.scan_master.manifest
        if (
            manifest.get("scan_master_revision_id") != self.scan_master.revision_id
            or manifest.get("project_id") != self.scan_master.project_id
            or manifest.get("authority_class") != "SCAN_MASTER"
            or manifest.get("output_geometry_sha256") != scan_digest
            or manifest.get("physical_accuracy_validation_status") != "DEFERRED_OWNER_VALIDATION"
            or manifest.get("mold_use_authorized") is not False
        ):
            raise DesignReviewError("scan_master_manifest_identity_or_authority_invalid")
        actual_digest = preview_geometry_sha256(self.design_preview)
        if self.design_preview_sha256 != actual_digest:
            raise DesignReviewError("design_preview_digest_mismatch")

    @classmethod
    def create(
        cls,
        scan_master: ScanMasterRevision,
        design_model: DesignModelRevision,
        design_preview: MeshGeometry,
    ) -> ScanDesignReviewBinding:
        return cls(
            scan_master,
            design_model,
            design_preview,
            preview_geometry_sha256(design_preview),
        )

    @property
    def is_exactly_scan_fitted(self) -> bool:
        return (
            self.design_model.fitted_to_scan_master_revision_id == self.scan_master.revision_id
            and self.design_model.scan_master_geometry_sha256 == mesh_sha256(self.scan_master.mesh)
        )

    def metadata(self) -> dict[str, object]:
        linked = self.is_exactly_scan_fitted
        return {
            "authority": "REVIEW_ONLY_NON_AUTHORITATIVE",
            "scan_master_revision_id": self.scan_master.revision_id,
            "scan_master_geometry_sha256": mesh_sha256(self.scan_master.mesh),
            "design_model_revision_id": self.design_model.revision_id,
            "design_model_preview_geometry_sha256": self.design_preview_sha256,
            "design_model_parent_scan_master_revision_id": self.design_model.fitted_to_scan_master_revision_id,
            "design_model_parent_scan_master_geometry_sha256": self.design_model.scan_master_geometry_sha256,
            "relationship": "EXACT_SCAN_MASTER_PARENT" if linked else "UNLINKED_OR_STANDALONE",
            "warning": "Visual comparison only; no fitting, measurement, edit, export, or physical-accuracy authority.",
        }


class ScanDesignReviewWidget(QWidget):
    """Small reusable Qt view; callers provide an exact source pair and display mesh."""

    def __init__(
        self,
        binding: ScanDesignReviewBinding,
        *,
        adapter: QtRasterViewportAdapter | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        if not isinstance(binding, ScanDesignReviewBinding):
            raise DesignReviewError("review_binding_required")
        self.binding = binding
        self.adapter = adapter or QtRasterViewportAdapter()
        self.mode = DesignReviewMode.SIDE_BY_SIDE
        self.scan_label = QLabel()
        self.design_label = QLabel()
        self.overlay_label = QLabel()
        self.scan_caption = QLabel("Scan Master · captured reference")
        self.design_caption = QLabel("Design Model · preview geometry")
        self.overlay_caption = QLabel("Scan Master (cyan) · Design Model preview (amber)")
        for label in (self.scan_label, self.design_label, self.overlay_label):
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setMinimumSize(220, 180)
        self.status_label = QLabel()
        self.mode_picker = QComboBox()
        self.mode_picker.addItem("Side by side", DesignReviewMode.SIDE_BY_SIDE.value)
        self.mode_picker.addItem("Ghosted overlay", DesignReviewMode.GHOSTED.value)
        self.mode_picker.currentIndexChanged.connect(self._select_mode)

        self.panel = QWidget(self)
        self.panel_layout = QHBoxLayout(self.panel)
        self.panel_layout.setContentsMargins(0, 0, 0, 0)
        self.scan_panel = QWidget(self.panel)
        scan_layout = QVBoxLayout(self.scan_panel)
        scan_layout.addWidget(self.scan_caption)
        scan_layout.addWidget(self.scan_label)
        self.design_panel = QWidget(self.panel)
        design_layout = QVBoxLayout(self.design_panel)
        design_layout.addWidget(self.design_caption)
        design_layout.addWidget(self.design_label)
        self.overlay_panel = QWidget(self.panel)
        overlay_layout = QVBoxLayout(self.overlay_panel)
        overlay_layout.addWidget(self.overlay_caption)
        overlay_layout.addWidget(self.overlay_label)
        self.panel_layout.addWidget(self.scan_panel)
        self.panel_layout.addWidget(self.design_panel)
        self.panel_layout.addWidget(self.overlay_panel)
        layout = QVBoxLayout(self)
        layout.addWidget(self.mode_picker)
        layout.addWidget(self.panel)
        layout.addWidget(self.status_label)
        self._refresh()

    def set_mode(self, mode: DesignReviewMode) -> None:
        if not isinstance(mode, DesignReviewMode):
            raise DesignReviewError("review_mode_invalid")
        if mode is DesignReviewMode.GHOSTED and not self.binding.is_exactly_scan_fitted:
            raise DesignReviewError("ghost_overlay_requires_exact_scan_master_parent")
        self.mode = mode
        self.mode_picker.setCurrentIndex(0 if mode is DesignReviewMode.SIDE_BY_SIDE else 1)
        self._refresh()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt override name
        super().resizeEvent(event)
        self._refresh()

    def _select_mode(self, index: int) -> None:
        mode = DesignReviewMode(self.mode_picker.itemData(index))
        if mode is DesignReviewMode.GHOSTED and not self.binding.is_exactly_scan_fitted:
            self.mode_picker.setCurrentIndex(0)
            self.status_label.setText(
                "Ghosting unavailable: Design Model is not bound to this exact Scan Master revision."
            )
            return
        self.mode = mode
        self._refresh()

    def _render_source(
        self,
        geometry: MeshGeometry,
        size: QSize,
        *,
        camera: ViewportCamera | None = None,
    ) -> QImage:
        scene = SceneModel()
        scene.add(SceneObject("review-source", SceneObjectKind.DESIGN_MODEL, geometry))
        state = ViewportState(
            camera=camera or ViewportCamera().fit(scene.bounds()),
            grid_visible=False,
            axes_visible=False,
            scale_cues_visible=False,
        )
        return self.adapter.render(scene, state, size)

    def _refresh(self) -> None:
        metadata = self.binding.metadata()
        relation = str(metadata["relationship"])
        scan_digest = str(metadata["scan_master_geometry_sha256"])
        design_digest = str(metadata["design_model_preview_geometry_sha256"])
        self.status_label.setText(
            "REVIEW ONLY · NON-AUTHORITATIVE · "
            + relation
            + " · Scan Master "
            + self.binding.scan_master.revision_id
            + " sha256:"
            + scan_digest
            + " · Design Model "
            + self.binding.design_model.revision_id
            + " sha256:"
            + design_digest
        )
        if self.mode is DesignReviewMode.SIDE_BY_SIDE:
            self.scan_caption.setText(
                "Scan Master · " + self.binding.scan_master.revision_id + " · sha256:" + scan_digest
            )
            self.design_caption.setText(
                "Design Model preview · "
                + self.binding.design_model.revision_id
                + " · sha256:"
                + design_digest
            )
            self.scan_label.setPixmap(
                QPixmap.fromImage(
                    self._render_source(self._scan_geometry(), self.scan_label.size())
                )
            )
            self.design_label.setPixmap(
                QPixmap.fromImage(
                    self._render_source(self.binding.design_preview, self.design_label.size())
                )
            )
            self.overlay_label.hide()
            self.overlay_panel.hide()
            self.scan_panel.show()
            self.design_panel.show()
            self.scan_label.show()
            self.design_label.show()
        else:
            self.scan_panel.hide()
            self.design_panel.hide()
            self.overlay_panel.show()
            self.overlay_label.show()
            self.overlay_caption.setText(
                "Ghosted review only · Scan Master sha256:"
                + scan_digest
                + " · Design Model sha256:"
                + design_digest
            )
            size = self.overlay_label.size()
            comparison_scene = SceneModel()
            comparison_scene.add(
                SceneObject("comparison-scan", SceneObjectKind.DESIGN_MODEL, self._scan_geometry())
            )
            comparison_scene.add(
                SceneObject(
                    "comparison-design", SceneObjectKind.DESIGN_MODEL, self.binding.design_preview
                )
            )
            common_camera = ViewportCamera().fit(comparison_scene.bounds())
            scan = self._render_source(self._scan_geometry(), size, camera=common_camera)
            design = self._render_source(self.binding.design_preview, size, camera=common_camera)
            self.overlay_label.setPixmap(QPixmap.fromImage(_ghost_composite(scan, design)))

    def _scan_geometry(self) -> MeshGeometry:
        mesh = self.binding.scan_master.mesh
        return MeshGeometry(mesh.vertices, mesh.triangles, mesh.vertex_normals or ())


def _ghost_composite(scan: QImage, design: QImage) -> QImage:
    """Recolor geometry pixels over the viewport's known flat background."""

    result = QImage(scan.size(), QImage.Format.Format_ARGB32)
    result.fill(_BACKGROUND)
    painter = QPainter(result)
    for image, color in ((scan, QColor("#38bdf8")), (design, QColor("#f59e0b"))):
        mask = QImage(image.size(), QImage.Format.Format_ARGB32)
        mask.fill(Qt.GlobalColor.transparent)
        for y in range(image.height()):
            for x in range(image.width()):
                pixel = image.pixelColor(x, y)
                if pixel != _BACKGROUND:
                    color_pixel = QColor(color)
                    color_pixel.setAlpha(pixel.alpha())
                    mask.setPixelColor(x, y, color_pixel)
        painter.setOpacity(0.62)
        painter.drawImage(0, 0, mask)
    painter.end()
    return result


__all__ = [
    "DesignReviewError",
    "DesignReviewMode",
    "ScanDesignReviewBinding",
    "ScanDesignReviewWidget",
    "preview_geometry_sha256",
]
