"""Library actions bar: create/link assets, backup/restore and contact sheet (PL-0460/0461)."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from shiboken6 import isValid

from packlab_core.design_model import PackageFamily
from packlab_core.packaging_asset import (
    AssetStatus,
    DesignModelLink,
    FieldProvenance,
    MeasurementUnit,
    PackagingAsset,
    PackagingFamily,
    PackagingMeasurement,
    ProvenanceClass,
    ScanMasterLink,
)
from packlab_core.reconstruction import ScaleState

from .design_workbench import DesignModelSession, DesignWorkbench
from .i18n import tr
from .packaging_library_backup import PackagingLibraryBackupService
from .packaging_library_browser import PackagingLibraryBrowserService, PackagingLibraryBrowserView
from .packaging_library_contact_sheet import PackagingLibraryContactSheetExporter
from .preferences import documents_folder  # F15 start folder, never the bare home

_FAMILY = {
    PackageFamily.JAR: PackagingFamily.JAR,
    PackageFamily.BOTTLE: PackagingFamily.BOTTLE,
    PackageFamily.TUBE: PackagingFamily.TUBE,
}
_ACTOR = "studio-user"


def design_model_link(session: DesignModelSession) -> DesignModelLink:
    model = session.model
    captured = model.standalone_root is None
    parent = (
        model.fitted_to_scan_master_revision_id if captured else model.standalone_root.revision_id  # type: ignore[union-attr]
    )
    return DesignModelLink(
        project_id=model.project_id,
        revision_id=model.revision_id,
        content_sha256=session.document_sha256,
        parent_authority_kind=model.parent_kind.value,
        parent_authority_revision_id=parent or "",
        scale_state=model.scale_state,
        scan_master_revision_id=model.fitted_to_scan_master_revision_id if captured else None,
        scan_master_geometry_sha256=model.scan_master_geometry_sha256 if captured else None,
    )


def scan_master_link(revision: Any) -> ScanMasterLink:
    """Link a persisted ``ScanMasterRevision`` (project authority) without copying geometry."""
    manifest = revision.manifest
    return ScanMasterLink(
        project_id=revision.project_id,
        revision_id=revision.revision_id,
        geometry_sha256=str(manifest["output_geometry_sha256"]),
        scale_state=ScaleState(str(manifest["scale_state"])),
        scale_provenance_id=str(manifest["scale_provenance_id"]),
    )


def asset_from_sources(
    asset_id: str,
    display_name: str,
    session: DesignModelSession | None,
) -> PackagingAsset:
    """Metadata-only asset; dimensions come from the Design Model BREP as PackLab estimates."""
    provenance = [
        FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
        FieldProvenance("status", ProvenanceClass.USER_DECLARED),
    ]
    values: dict[str, Any] = {}
    if session is not None:
        family = _FAMILY.get(session.model.package_family)
        if family is not None:
            values["family"] = family
            provenance.append(
                FieldProvenance(
                    "family", ProvenanceClass.PACKLAB_ESTIMATE, method_id="design-model-family"
                )
            )
        x0, _y0, z0, x1, _y1, z1 = session.bounds_mm
        values["overall_height"] = PackagingMeasurement(z1 - z0, MeasurementUnit.MILLIMETER)
        values["body_diameter"] = PackagingMeasurement(x1 - x0, MeasurementUnit.MILLIMETER)
        for name in ("overall_height", "body_diameter"):
            provenance.append(
                FieldProvenance(
                    name,
                    ProvenanceClass.PACKLAB_ESTIMATE,
                    method_id="design-model-brep-bounds-mm-unverified",
                )
            )
    return PackagingAsset(
        asset_id=asset_id,
        display_name=display_name,
        family=values.pop("family", PackagingFamily.UNKNOWN),
        status=AssetStatus.DRAFT,
        field_provenance=tuple(provenance),
        **values,
    )


class LibraryActionsBar(QWidget):
    """Adds the missing write actions on top of the existing read-only library browser."""

    def __init__(
        self,
        browser: PackagingLibraryBrowserView,
        service: PackagingLibraryBrowserService,
        workbench: DesignWorkbench,
        *,
        scan_master_provider: Callable[[], Any] = lambda: None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("packlab.library.actions")
        self.browser = browser
        self.service = service
        self.workbench = workbench
        self.scan_master_provider = scan_master_provider
        self.backup_service = PackagingLibraryBackupService()
        self.last_result: object = None
        self.choose_backup_path: Callable[[], str] = lambda: QFileDialog.getSaveFileName(
            self,
            "Back up Packaging Library",
            str(documents_folder() / "packlab-library-backup.zip"),
            "Library backup (*.zip)",
        )[0]
        self.choose_archive_path: Callable[[], str] = lambda: QFileDialog.getOpenFileName(
            self,
            "Restore Packaging Library backup",
            str(documents_folder()),
            "Library backup (*.zip)",
        )[0]
        self.choose_directory: Callable[[str], str] = lambda title: (
            QFileDialog.getExistingDirectory(self, title, str(documents_folder()))
        )

        self.asset_id = QLineEdit(self)
        self.asset_id.setObjectName("packlab.library.new-asset.id")
        self.asset_id.setPlaceholderText("e.g. jar-500ml-a1b2c3d4")
        self.asset_name = QLineEdit(self)
        self.asset_name.setObjectName("packlab.library.new-asset.name")
        self.asset_name.setPlaceholderText("e.g. Jar 500 ml")
        self.create_button = self._button("Add to library", "new-asset.create", self.create_asset)
        self.backup_button = self._button("Back up library…", "backup", self.backup)
        self.restore_button = self._button("Restore backup into folder…", "restore", self.restore)
        self.contact_button = self._button(
            "Export contact sheet…", "contact-sheet", self.export_contact_sheet
        )
        self.status = QLabel(
            "Create SKU uses the selected asset; artwork comes from the Labels tab.", self
        )
        self.status.setObjectName("packlab.library.actions-status")
        self.status.setWordWrap(True)
        self.status.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        create_row = QFormLayout()  # labelled fields (PL-0464)
        create_row.addRow("Asset ID", self.asset_id)
        create_row.addRow("Display name", self.asset_name)
        create_button_row = QHBoxLayout()
        create_button_row.addWidget(self.create_button)
        create_button_row.addStretch(1)
        create_row.addRow("", create_button_row)
        file_row = QGridLayout()  # two columns: fits 1280 px screens in Turkish too
        file_row.addWidget(self.backup_button, 0, 0)
        file_row.addWidget(self.restore_button, 0, 1)
        file_row.addWidget(self.contact_button, 1, 0)
        file_row.setColumnStretch(2, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(create_row)
        layout.addLayout(file_row)
        layout.addWidget(self.status)
        workbench.changed.connect(self._prefill)
        # F12: impossible actions are disabled, with the reason in the tooltip.
        workbench.changed.connect(self.update_enabled)
        browser.item_view.currentItemChanged.connect(lambda *_args: self.update_enabled())
        model = browser.item_view.model()
        model.rowsInserted.connect(lambda *_args: self.update_enabled())
        model.rowsRemoved.connect(lambda *_args: self.update_enabled())
        model.modelReset.connect(lambda *_args: self.update_enabled())
        self._prefill()
        self.update_enabled()

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.update_enabled()  # the project's Scan Master may have changed meanwhile

    def update_enabled(self) -> None:
        if not isValid(self) or not isValid(self.browser.item_view):
            return  # model signals can fire while the window is being destroyed
        can_add = self.workbench.session is not None or self._scan_master() is not None
        self.create_button.setEnabled(can_add)
        self.create_button.setToolTip(
            tr("Adds the open Design Model and the project's Scan Master as a library asset.")
            if can_add
            else tr(
                "Open a Design Model (Labels page) or promote a Scan Master in the project first."
            )
        )
        selected = self.browser.selected_asset_id is not None
        self.browser.create_sku_button.setEnabled(selected)
        self.browser.create_sku_button.setToolTip(
            "" if selected else tr("Select a packaging asset in the list first.")
        )
        has_assets = self.browser.item_view.count() > 0
        self.contact_button.setEnabled(has_assets)
        self.contact_button.setToolTip(
            "" if has_assets else tr("The library is empty: add an asset first.")
        )

    def _button(self, text: str, name: str, slot: Callable[[], object]) -> QPushButton:
        button = QPushButton(text, self)
        button.setObjectName(f"packlab.library.{name}")
        button.clicked.connect(lambda _checked=False: slot())
        return button

    def _prefill(self) -> None:
        session = self.workbench.session
        if session is None:
            return
        slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", session.part_name).strip("-.") or "asset"
        if not slug[0].isalpha():
            slug = f"asset-{slug}"
        self.asset_id.setText(f"{slug[:100]}-{session.model.revision_id[-8:]}")
        self.asset_name.setText(session.part_name)

    def _scan_master(self) -> Any:
        try:
            return self.scan_master_provider()
        except Exception:
            return None

    # ------------------------------------------------------------------ actions
    def create_asset(self) -> None:
        session = self.workbench.session
        scan = self._scan_master()
        if session is None and scan is None:
            self.status.setText(
                "Open a Design Model (Labels tab) or select a Scan Master in the project first."
            )
            return
        try:
            store = self.service.audit_store
            asset = asset_from_sources(
                self.asset_id.text().strip(), self.asset_name.text().strip(), session
            )
            created = store.create_asset(
                asset,
                expected_state_revision=store.snapshot().state_revision,
                actor_id=_ACTOR,
                reason="Create a Packaging Asset from Studio design sources.",
            )
            links = (design_model_link(session),) if session is not None else ()
            linked = asset.with_source_links(
                raw_scan_links=(),
                scan_master_link=scan_master_link(scan) if scan is not None else None,
                design_model_links=links,
                preferred_design_model_revision_id=links[0].revision_id if links else None,
            )
            store.link_source(
                linked,
                expected_state_revision=created.state_revision,
                expected_asset_revision_id=asset.revision_id,
                actor_id=_ACTOR,
                reason="Link the exact Design Model and Scan Master revisions.",
            )
        except Exception as error:
            self.status.setText(f"Asset not created: {error}")
            return
        self.browser.refresh()
        for index in range(self.browser.item_view.count()):
            item = self.browser.item_view.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == linked.asset_id:
                self.browser.item_view.setCurrentItem(item)
        sources = [
            name
            for name, present in (("Design Model", session), ("Scan Master", scan))
            if present is not None
        ]
        self.status.setText(
            f"Created {linked.asset_id} linked to {' + '.join(sources)}; "
            "select it and use Create SKU to attach label artwork."
        )

    def backup(self) -> None:
        path = self.choose_backup_path()
        if not path:
            return
        try:
            report = self.backup_service.create_backup(self.service.library_root, path)
        except Exception as error:
            self.status.setText(f"Backup failed: {error}")
            return
        self.last_result = report
        self.status.setText(
            f"Backup written: {path} ({len(report.files)} files, sha256 "
            f"{report.archive_sha256[:12]}…, state {report.library_state_revision[-12:]})."
        )

    def restore(self) -> None:
        archive = self.choose_archive_path()
        if not archive:
            return
        folder = self.choose_directory("Restore into an empty folder")
        if not folder:
            return
        try:
            report = self.backup_service.restore(archive, folder)
        except Exception as error:
            self.status.setText(f"Restore failed: {error}")
            return
        self.last_result = report
        self.status.setText(
            f"Restored {len(report.files)} files into {folder}; library state "
            f"{report.library_state_revision[-12:]} verified."
        )

    def export_contact_sheet(self) -> None:
        folder = self.choose_directory("Export contact sheet into folder")
        if not folder:
            return
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        try:
            export = PackagingLibraryContactSheetExporter(self.service).export(
                Path(folder) / f"packlab-contact-sheet-{stamp}"
            )
        except Exception as error:
            self.status.setText(f"Contact sheet failed: {error}")
            return
        self.last_result = export
        self.status.setText(
            f"Contact sheet written: {export.contact_sheet_path} ({len(export.tiles)} assets)."
        )


__all__ = [
    "LibraryActionsBar",
    "asset_from_sources",
    "design_model_link",
    "scan_master_link",
]
