"""Thin Qt presentation for core-owned manual mask correction."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt, Signal
from PySide6.QtGui import QColor, QMouseEvent, QPainter, QPaintEvent
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from packlab_core.manual_mask_correction import (
    ManualMaskCorrectionService,
    ManualMaskEdit,
    ManualMaskEditAction,
)
from packlab_core.segmentation import MaskArtifact, MaskRaster


class MaskCanvas(QWidget):
    """Display the parent mask and report clicked mask-grid coordinates."""

    pixel_clicked = Signal(int, int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(320, 240)
        self._raster: MaskRaster | None = None

    def set_raster(self, raster: MaskRaster | None) -> None:
        self._raster = raster
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#292929"))
        if self._raster is None:
            return
        width, height = self._raster.width, self._raster.height
        scale = min(self.width() / width, self.height() / height)
        left = (self.width() - width * scale) / 2
        top = (self.height() - height * scale) / 2
        for y in range(height):
            for x in range(width):
                color = (
                    QColor("#35c759") if self._raster.values[y * width + x] else QColor(0, 0, 0, 0)
                )
                painter.fillRect(QRectF(left + x * scale, top + y * scale, scale, scale), color)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._raster is None or event.button() != Qt.MouseButton.LeftButton:
            return
        width, height = self._raster.width, self._raster.height
        scale = min(self.width() / width, self.height() / height)
        left = (self.width() - width * scale) / 2
        top = (self.height() - height * scale) / 2
        point: QPointF = event.position()
        grid_x = (point.x() - left) / scale
        grid_y = (point.y() - top) / scale
        if 0 <= grid_x < width and 0 <= grid_y < height:
            x, y = int(grid_x), int(grid_y)
            self.pixel_clicked.emit(x, y)


class MaskCorrectionView(QWidget):
    """Collect session edits; only the injected domain service creates revisions."""

    child_created = Signal(object)
    cancelled = Signal()
    correction_rejected = Signal(str)

    def __init__(
        self,
        *,
        correction_service: ManualMaskCorrectionService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.view.mask-correction")
        self.correction_service = correction_service or ManualMaskCorrectionService()
        self._parent_artifact: MaskArtifact | None = None
        self._editor_id: str | None = None
        self._created_at: str | None = None
        self._operations: list[ManualMaskEdit] = []
        self.canvas = MaskCanvas(self)
        self.canvas.setObjectName("packlab.mask-correction.canvas")
        self.mode = QComboBox(self)
        self.mode.addItem("Paint foreground", ManualMaskEditAction.PAINT.value)
        self.mode.addItem("Erase to background", ManualMaskEditAction.ERASE.value)
        self.status = QLabel("Open a mask correction session to begin.", self)
        self.submit_button = QPushButton("Submit correction", self)
        self.cancel_button = QPushButton("Cancel", self)
        self.undo_button = QPushButton("Undo", self)
        actions = QHBoxLayout()
        actions.addWidget(self.mode)
        actions.addWidget(self.undo_button)
        actions.addWidget(self.submit_button)
        actions.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        layout.addLayout(actions)
        layout.addWidget(self.status)
        self.canvas.pixel_clicked.connect(self.add_pixel_edit)
        self.undo_button.clicked.connect(self.undo)
        self.submit_button.clicked.connect(self.submit)
        self.cancel_button.clicked.connect(self.cancel)
        self._set_session_enabled(False)

    def begin(self, parent: MaskArtifact, *, editor_id: str, created_at: str) -> None:
        if parent.raster is None:
            raise ValueError("mask correction requires an in-memory raster")
        self._parent_artifact = parent
        self._editor_id = editor_id
        self._created_at = created_at
        self._operations.clear()
        self.canvas.set_raster(parent.raster)
        self.status.setText("Select pixels, then submit or cancel.")
        self._set_session_enabled(True)

    def add_pixel_edit(self, x: int, y: int) -> None:
        if self._parent_artifact is None:
            return
        try:
            operation = ManualMaskEdit(x, y, ManualMaskEditAction(self.mode.currentData()))
        except ValueError as error:
            self.correction_rejected.emit(str(error))
            return
        self._operations.append(operation)
        if self._parent_artifact.raster is not None:
            values = list(self._parent_artifact.raster.values)
            for edit in self._operations:
                values[edit.y * self._parent_artifact.mask_width + edit.x] = (
                    edit.action is ManualMaskEditAction.PAINT
                )
            self.canvas.set_raster(
                MaskRaster(
                    self._parent_artifact.mask_width,
                    self._parent_artifact.mask_height,
                    tuple(values),
                )
            )
        self.status.setText(f"{len(self._operations)} unsubmitted pixel edit(s)")

    def undo(self) -> None:
        if self._operations:
            self._operations.pop()
            self._refresh_preview()

    def submit(self) -> None:
        if self._parent_artifact is None or self._editor_id is None or self._created_at is None:
            return
        try:
            child = self.correction_service.correct(
                self._parent_artifact,
                editor_id=self._editor_id,
                operations=tuple(self._operations),
                created_at=self._created_at,
            )
        except (ValueError, TypeError) as error:
            self.status.setText(str(error))
            self.correction_rejected.emit(str(error))
            return
        self._end_session()
        self.child_created.emit(child)

    def cancel(self) -> None:
        self._end_session()
        self.cancelled.emit()

    def _refresh_preview(self) -> None:
        parent = self._parent_artifact
        if parent is None or parent.raster is None:
            return
        values = list(parent.raster.values)
        for edit in self._operations:
            values[edit.y * parent.mask_width + edit.x] = edit.action is ManualMaskEditAction.PAINT
        self.canvas.set_raster(MaskRaster(parent.mask_width, parent.mask_height, tuple(values)))
        self.status.setText(f"{len(self._operations)} unsubmitted pixel edit(s)")

    def _end_session(self) -> None:
        self._parent_artifact = None
        self._editor_id = None
        self._created_at = None
        self._operations.clear()
        self.canvas.set_raster(None)
        self.status.setText("No active mask correction session.")
        self._set_session_enabled(False)

    def _set_session_enabled(self, enabled: bool) -> None:
        self.mode.setEnabled(enabled)
        self.submit_button.setEnabled(enabled)
        self.cancel_button.setEnabled(enabled)
        self.undo_button.setEnabled(enabled)
