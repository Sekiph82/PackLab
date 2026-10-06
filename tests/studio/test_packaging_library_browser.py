from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path

import pytest
from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QPushButton
from tests.core.test_packaging_asset import _asset

from packlab_core.packaging_asset import (
    AssetStatus,
    BaseMaterial,
    ClosureType,
    DesignModelLink,
    MeasurementUnit,
    PackagingFamily,
    PackagingMeasurement,
    RawScanLink,
    ScaleState,
)
from packlab_core.packaging_sku_library import (
    PackagingSkuStatus,
    SkuArtworkPresentationReference,
)
from packlab_studio import packaging_library_browser as browser
from packlab_studio.app import create_application
from packlab_studio.navigation import Route
from packlab_studio.packaging_library_audit import PackagingLibraryAuditStore
from packlab_studio.packaging_library_browser import (
    BrowserDisplayState,
    CreatePackagingSkuDialog,
    LibraryRelatedRecord,
    LibraryThumbnailReference,
    PackagingLibraryBrowserError,
    PackagingLibraryBrowserService,
    PackagingLibraryBrowserView,
    PackagingLibraryFilters,
    PreviewState,
    ProjectPreviewResolution,
    ThumbnailSource,
)
from packlab_studio.shell import StudioMainWindow

NOW = datetime(2026, 10, 5, 14, 0, tzinfo=UTC)


def test_design_model_link_parser_checks_optional_parent_fields() -> None:
    link = DesignModelLink(
        project_id="water-project",
        revision_id="design-model-rev-1",
        content_sha256="c" * 64,
        parent_authority_kind="STANDALONE_DESIGN_GEOMETRY",
        parent_authority_revision_id="standalone-root-1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
    )
    assert browser._design_model_link_from_dict(link.as_dict()) == link
    malformed = link.as_dict()
    malformed["mold_use_authorized"] = "false"
    with pytest.raises(PackagingLibraryBrowserError, match="design_model_link_invalid"):
        browser._design_model_link_from_dict(malformed)


def _png(path: Path, color: Qt.GlobalColor = Qt.GlobalColor.darkBlue) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    image = QImage(32, 24, QImage.Format.Format_RGB32)
    image.fill(color)
    assert image.save(str(path), "PNG")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _library(root: Path, *, assets: tuple | None = None) -> PackagingLibraryAuditStore:
    store = PackagingLibraryAuditStore(root, clock=lambda: NOW)
    for asset in assets or (_asset(),):
        snapshot = store.snapshot()
        store.create_asset(
            asset,
            expected_state_revision=snapshot.state_revision,
            actor_id="operator-1",
            reason="Add package metadata to local library",
        )
    return store


def test_route_library_renders_without_project_and_mode_refresh_keep_selection(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-browser-route-test"])
    assets = (
        _asset(asset_id="water-red", display_name="Red Water Bottle"),
        _asset(asset_id="water-blue", display_name="Blue Water Bottle"),
    )
    audit_store = _library(tmp_path / "library", assets=assets)
    service = PackagingLibraryBrowserService(audit_store, tmp_path / "library")
    window = StudioMainWindow(packaging_library_service=service)
    view = window.route_stack.views[Route.LIBRARY]

    assert isinstance(view, PackagingLibraryBrowserView)
    assert window.project_manager.current is None
    assert view.isEnabled()
    assert view.display_state is BrowserDisplayState.READY
    assert view.item_view.count() == 2
    assert view.item_view.viewMode() == view.item_view.ViewMode.IconMode
    view.item_view.setCurrentRow(1)
    selected = view.selected_asset_id
    before_revisions = tuple(item.revision_id for item in audit_store.snapshot().assets)

    view.mode_selector.setCurrentIndex(1)
    assert view.item_view.viewMode() == view.item_view.ViewMode.ListMode
    assert view.selected_asset_id == selected
    view.refresh_button.click()

    assert view.selected_asset_id == selected
    assert view.display_state is BrowserDisplayState.READY
    assert tuple(item.revision_id for item in audit_store.snapshot().assets) == before_revisions
    window.navigation.navigate(Route.LIBRARY)
    assert window.route_stack.currentWidget() is view
    window.close()
    app.processEvents()


def test_empty_and_error_states_are_visible_and_refresh_recovers(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-browser-state-test"])
    empty_service = PackagingLibraryBrowserService(
        PackagingLibraryAuditStore(tmp_path / "empty"), tmp_path / "empty"
    )
    empty = PackagingLibraryBrowserView(empty_service)
    assert empty.display_state is BrowserDisplayState.EMPTY
    assert empty.state_message.text() == "No packaging assets in this library."

    class FailingService:
        def list_assets(self):
            raise PackagingLibraryBrowserError("simulated unavailable library")

    failed = PackagingLibraryBrowserView(FailingService())  # type: ignore[arg-type]
    assert failed.display_state is BrowserDisplayState.ERROR
    assert "simulated unavailable library" in failed.state_message.text()

    loading_states: list[BrowserDisplayState] = []

    class LoadingAwareService:
        def list_assets(self):
            loading_states.append(recovered.display_state)
            return ()

    recovered = PackagingLibraryBrowserView(empty_service)
    recovered.service = LoadingAwareService()  # type: ignore[assignment]
    recovered.refresh()
    assert loading_states == [BrowserDisplayState.LOADING]
    assert recovered.display_state is BrowserDisplayState.EMPTY
    empty.close()
    failed.close()
    recovered.close()
    app.processEvents()


def test_digest_bound_local_thumbnail_and_malformed_missing_fallback(tmp_path: Path) -> None:
    app = create_application(["packlab-library-browser-thumbnail-test"])
    library_root = tmp_path / "library"
    audit_store = _library(library_root)
    staged_image = tmp_path / "staged-thumbnail.png"
    digest = _png(staged_image, Qt.GlobalColor.darkGreen)
    image_path = library_root / "thumbnails" / "sha256" / digest[:2] / (digest + ".png")
    image_path.parent.mkdir(parents=True, exist_ok=True)
    staged_image.replace(image_path)
    reference = LibraryThumbnailReference(
        sha256=digest,
        media_type="image/png",
        relative_path=f"thumbnails/sha256/{digest[:2]}/{digest}.png",
        source=ThumbnailSource.LIBRARY,
    )
    service = PackagingLibraryBrowserService(
        audit_store,
        library_root,
        thumbnail_reference_provider=lambda _asset_id: reference,
    )
    view = PackagingLibraryBrowserView(service)
    summary = service.list_assets()[0]
    assert service.resolve_thumbnail(summary) == image_path
    valid_icon = view.item_view.item(0).icon().pixmap(QSize(128, 96)).toImage()
    assert not valid_icon.isNull()

    image_path.write_bytes(b"tampered thumbnail")
    view.refresh()
    fallback_icon = view.item_view.item(0).icon().pixmap(QSize(128, 96)).toImage()
    assert not fallback_icon.isNull()
    assert fallback_icon != valid_icon
    assert service.resolve_thumbnail(service.list_assets()[0]) is None

    remote_service = PackagingLibraryBrowserService(
        audit_store,
        library_root,
        thumbnail_reference_provider=lambda _asset_id: "https://example.invalid/preview.png",  # type: ignore[return-value]
    )
    assert remote_service.list_assets()[0].thumbnail_reference is None
    with pytest.raises(PackagingLibraryBrowserError, match="path_invalid"):
        LibraryThumbnailReference(
            sha256="b" * 64,
            media_type="image/png",
            relative_path="../../outside.png",
            source=ThumbnailSource.PROJECT,
            project_id="project-1",
            revision_id="revision-1",
        )
    view.close()
    app.processEvents()


def test_project_thumbnail_requires_an_exact_asset_source_link(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    project_root = tmp_path / "project"
    thumb_path = project_root / "derived" / "thumb.png"
    digest = _png(thumb_path)
    linked = _asset().with_source_links(
        raw_scan_links=(RawScanLink("project-1", "raw-rev-1", "a" * 64),),
        scan_master_link=None,
        design_model_links=(),
    )
    audit_store = _library(library_root, assets=(linked,))
    reference = LibraryThumbnailReference(
        sha256=digest,
        media_type="image/png",
        relative_path="derived/thumb.png",
        source=ThumbnailSource.PROJECT,
        project_id="project-1",
        revision_id="raw-rev-1",
    )
    service = PackagingLibraryBrowserService(
        audit_store,
        library_root,
        thumbnail_reference_provider=lambda _asset_id: reference,
        project_root_resolver=lambda project_id: (
            project_root if project_id == "project-1" else None
        ),
    )
    summary = service.list_assets()[0]
    assert service.resolve_thumbnail(summary) == thumb_path

    stale_reference = LibraryThumbnailReference(
        sha256=digest,
        media_type="image/png",
        relative_path="derived/thumb.png",
        source=ThumbnailSource.PROJECT,
        project_id="project-1",
        revision_id="stale-revision",
    )
    stale_service = PackagingLibraryBrowserService(
        audit_store,
        library_root,
        thumbnail_reference_provider=lambda _asset_id: stale_reference,
        project_root_resolver=lambda _project_id: project_root,
    )
    assert stale_service.list_assets()[0].thumbnail_reference is None


def test_search_matches_id_name_supplier_and_family_with_stable_unicode_order(
    tmp_path: Path,
) -> None:
    library_root = tmp_path / "library"
    assets = (
        _asset(
            asset_id="juice-carton",
            display_name="Café Juice Carton",
            family=PackagingFamily.CARTON,
            supplier_id="sup-002",
            supplier_name="Ｆｏｏ Packaging",
        ),
        _asset(
            asset_id="water-bottle",
            display_name="Aqua Bottle",
            family=PackagingFamily.BOTTLE,
            supplier_id="bottle-vendor",
            supplier_name="Bottle Vendor",
        ),
    )
    store = _library(library_root, assets=assets)
    service = PackagingLibraryBrowserService(store, library_root)

    ordered = service.search_assets("")
    assert [item.asset_id for item in ordered] == ["water-bottle", "juice-carton"]
    original_revisions = tuple(item.revision_id for item in store.snapshot().assets)
    assert [item.asset_id for item in service.search_assets("WATER-BOTTLE")] == ["water-bottle"]
    assert [item.asset_id for item in service.search_assets("aQuA")] == ["water-bottle"]
    assert [item.asset_id for item in service.search_assets("vendor")] == ["water-bottle"]
    assert [item.asset_id for item in service.search_assets("SUP-002")] == ["juice-carton"]
    assert [item.asset_id for item in service.search_assets("carton")] == ["juice-carton"]
    assert [item.asset_id for item in service.search_assets("cafe")] == []
    assert [item.asset_id for item in service.search_assets("Café")] == ["juice-carton"]
    assert [item.asset_id for item in service.search_assets("ＣＡＦÉ")] == ["juice-carton"]
    assert [item.asset_id for item in service.search_assets("foo")] == ["juice-carton"]
    assert len(service.search_assets("bottle")) == 1
    with pytest.raises(PackagingLibraryBrowserError, match="too_long"):
        service.search_assets("x" * 129)
    assert tuple(item.revision_id for item in store.snapshot().assets) == original_revisions


def test_search_field_updates_visible_results_and_clearing_restores_library(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-browser-search-test"])
    library_root = tmp_path / "library"
    store = _library(
        library_root,
        assets=(
            _asset(asset_id="water-one", display_name="Water Bottle"),
            _asset(asset_id="juice-one", display_name="Juice Bottle"),
        ),
    )
    service = PackagingLibraryBrowserService(store, library_root)
    view = PackagingLibraryBrowserView(service)
    before = tuple((item.asset_id, item.revision_id) for item in store.snapshot().assets)

    view.search_field.setText("juice")
    assert view.item_view.count() == 1
    assert view.item_view.item(0).data(Qt.ItemDataRole.UserRole) == "juice-one"
    view.search_field.clear()
    assert view.item_view.count() == 2
    assert tuple((item.asset_id, item.revision_id) for item in store.snapshot().assets) == before
    view.close()
    app.processEvents()


def test_composable_filters_keep_explicit_units_unknowns_and_provenance(
    tmp_path: Path,
) -> None:
    library_root = tmp_path / "library"
    assets = (
        _asset(
            asset_id="water-500ml",
            display_name="Water bottle",
            nominal_volume=PackagingMeasurement(500, MeasurementUnit.MILLILITER),
            base_material=BaseMaterial.PET,
            closure_type=ClosureType.SCREW_CAP,
            status=AssetStatus.ACTIVE,
        ),
        _asset(
            asset_id="water-half-liter",
            display_name="Water bottle liter",
            nominal_volume=PackagingMeasurement(0.5, MeasurementUnit.LITER),
            base_material=BaseMaterial.PET,
            closure_type=ClosureType.FLIP_TOP,
            status=AssetStatus.ACTIVE,
        ),
        _asset(
            asset_id="mystery-pack",
            display_name="Mystery package",
            nominal_volume=None,
            base_material=BaseMaterial.UNKNOWN,
            closure_type=ClosureType.UNKNOWN,
            status=AssetStatus.UNKNOWN,
        ),
    )
    store = _library(library_root, assets=assets)
    service = PackagingLibraryBrowserService(store, library_root)
    all_assets = service.list_assets()
    original_revisions = tuple(item.revision_id for item in store.snapshot().assets)
    assert [item.asset_id for item in service.filter_assets(tuple(reversed(all_assets)))] == [
        "mystery-pack",
        "water-500ml",
        "water-half-liter",
    ]

    combined = service.filter_assets(
        all_assets,
        query="water",
        filters=PackagingLibraryFilters(
            nominal_volume=(500, "mL"),
            material="PET",
            closure="SCREW_CAP",
            status="ACTIVE",
        ),
    )
    assert [item.asset_id for item in combined] == ["water-500ml"]
    assert dict(combined[0].field_provenance)["nominal_volume"] == "USER_DECLARED"
    assert [
        item.asset_id
        for item in service.filter_assets(
            all_assets,
            filters=PackagingLibraryFilters(nominal_volume=(0.5, "L")),
        )
    ] == ["water-half-liter"]
    assert [
        item.asset_id
        for item in service.filter_assets(
            all_assets,
            filters=PackagingLibraryFilters(nominal_volume="UNKNOWN"),
        )
    ] == ["mystery-pack"]
    unknown = service.filter_assets(
        all_assets,
        filters=PackagingLibraryFilters(
            nominal_volume="UNKNOWN",
            material="UNKNOWN",
            closure="UNKNOWN",
            status="UNKNOWN",
        ),
    )
    assert [item.asset_id for item in unknown] == ["mystery-pack"]
    assert "nominal_volume" not in dict(unknown[0].field_provenance)
    assert [
        item.asset_id
        for item in service.filter_assets(
            all_assets,
            filters=PackagingLibraryFilters(material="PET", status="UNKNOWN"),
        )
    ] == []
    with pytest.raises(PackagingLibraryBrowserError, match="explicit_value_and_unit"):
        PackagingLibraryFilters(nominal_volume=(500, ""))
    assert tuple(item.revision_id for item in store.snapshot().assets) == original_revisions


def test_filter_controls_compose_with_search_and_clear_to_search_only(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-browser-filter-test"])
    library_root = tmp_path / "library"
    store = _library(
        library_root,
        assets=(
            _asset(
                asset_id="water-pet", display_name="Water bottle", base_material=BaseMaterial.PET
            ),
            _asset(
                asset_id="water-glass", display_name="Water jar", base_material=BaseMaterial.GLASS
            ),
            _asset(
                asset_id="juice-pet", display_name="Juice bottle", base_material=BaseMaterial.PET
            ),
        ),
    )
    service = PackagingLibraryBrowserService(store, library_root)
    view = PackagingLibraryBrowserView(service)
    view.search_field.setText("water")
    pet_index = view.material_filter.findData("PET")
    assert pet_index >= 0
    view.material_filter.setCurrentIndex(pet_index)
    assert view.item_view.count() == 1
    assert view.item_view.item(0).data(Qt.ItemDataRole.UserRole) == "water-pet"

    view.clear_filters_button.click()
    assert view.search_field.text() == "water"
    assert view.item_view.count() == 2
    assert [
        view.item_view.item(index).data(Qt.ItemDataRole.UserRole)
        for index in range(view.item_view.count())
    ] == ["water-pet", "water-glass"]
    view.close()
    app.processEvents()


def test_detail_view_renders_verified_linked_preview_and_related_records(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-browser-detail-test"])
    project_root = tmp_path / "project"
    mesh_path = project_root / "meshes" / "water.obj"
    mesh_path.parent.mkdir(parents=True)
    mesh_bytes = b"v 0 0 0\nv 1 0 0\nv 0 1 0\nf 1 2 3\n"
    mesh_path.write_bytes(mesh_bytes)
    mesh_digest = hashlib.sha256(mesh_bytes).hexdigest()
    linked_asset = _asset().with_source_links(
        raw_scan_links=(RawScanLink("project-detail", "scan-revision-1", mesh_digest),),
        scan_master_link=None,
        design_model_links=(),
    )
    library_root = tmp_path / "library"
    store = _library(library_root, assets=(linked_asset,))
    related_records = (
        LibraryRelatedRecord("COMPONENT", "cap-28mm", "28 mm Cap", "cap-rev-1"),
        LibraryRelatedRecord("ARTWORK", "artwork-water", "Water Label", "art-rev-2"),
        LibraryRelatedRecord("SKU", "sku-water-500", "Water 500 mL", "sku-rev-4"),
    )
    resolutions: list[tuple[str, str, str]] = []

    def resolve(reference):
        resolutions.append((reference.project_id, reference.revision_id, reference.sha256))
        return ProjectPreviewResolution(project_root, "meshes/water.obj", mesh_digest)

    service = PackagingLibraryBrowserService(
        store,
        library_root,
        preview_resolver=resolve,
        related_records_resolver=lambda _asset_id: related_records,
    )
    view = PackagingLibraryBrowserView(service)
    view.item_view.setCurrentRow(0)

    assert resolutions == [("project-detail", "scan-revision-1", mesh_digest)]
    assert "scan-revision-1" in view.detail_text.toPlainText()
    assert "USER_DECLARED" in view.detail_text.toPlainText()
    assert "28 mm Cap" in view.detail_text.toPlainText()
    assert "Water Label" in view.detail_text.toPlainText()
    assert "Water 500 mL" in view.detail_text.toPlainText()
    assert view.preview_label.pixmap() is not None
    assert not view.preview_label.pixmap().isNull()
    before_revision = store.snapshot().assets[0].revision_id
    assert mesh_path.read_bytes() == mesh_bytes

    mesh_path.write_bytes(b"stale geometry")
    detail = service.asset_detail(service.list_assets()[0])
    stale = service.render_preview(detail)
    assert stale.state is PreviewState.STALE
    assert store.snapshot().assets[0].revision_id == before_revision
    view.close()
    app.processEvents()


def test_detail_without_runtime_project_resolver_shows_unavailable_state(tmp_path: Path) -> None:
    library_root = tmp_path / "library"
    asset = _asset().with_source_links(
        raw_scan_links=(RawScanLink("offline-project", "scan-revision-9", "c" * 64),),
        scan_master_link=None,
        design_model_links=(),
    )
    service = PackagingLibraryBrowserService(_library(library_root, assets=(asset,)), library_root)
    detail = service.asset_detail(service.list_assets()[0])
    preview = service.render_preview(detail)
    assert preview.state is PreviewState.UNAVAILABLE
    assert detail.raw_scans[0].revision_id == "scan-revision-9"


def test_relationship_badges_sections_and_navigation_keep_assets_separate(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-browser-relationships-test"])
    library_root = tmp_path / "library"
    store = _library(
        library_root,
        assets=(
            _asset(asset_id="asset-alpha", display_name="Alpha package"),
            _asset(asset_id="asset-beta", display_name="Beta package"),
        ),
    )
    revisions = {item.asset_id: item.revision_id for item in store.snapshot().assets}
    snapshot = store.snapshot()
    store.create_relationship(
        "DUPLICATE",
        "asset-alpha",
        "asset-beta",
        expected_state_revision=snapshot.state_revision,
        expected_asset_revisions=(
            ("asset-alpha", revisions["asset-alpha"]),
            ("asset-beta", revisions["asset-beta"]),
        ),
        actor_id="operator-1",
        reason="Owner confirmed equivalent package metadata",
        provenance_class="USER_DECLARED",
    )
    service = PackagingLibraryBrowserService(store, library_root)
    view = PackagingLibraryBrowserView(service)
    alpha_row = next(
        row
        for row in range(view.item_view.count())
        if view.item_view.item(row).data(Qt.ItemDataRole.UserRole) == "asset-alpha"
    )
    view.item_view.setCurrentRow(alpha_row)
    assert "DUPLICATE" in view.item_view.item(alpha_row).text()
    assert view.related_asset_view.count() == 1
    assert "asset-beta" in view.related_asset_view.item(0).text()
    assert "USER_DECLARED" in view.detail_text.toPlainText()

    view.search_field.setText("asset-alpha")
    view.related_asset_view.itemClicked.emit(view.related_asset_view.item(0))
    assert view.search_field.text() == ""
    assert view.selected_asset_id == "asset-beta"
    assert {item.asset_id: item.revision_id for item in store.snapshot().assets} == revisions
    view.close()
    app.processEvents()


def test_create_sku_reuses_exact_geometry_and_keeps_artwork_separate(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-create-sku-test"])
    library_root = tmp_path / "library"
    design_model = DesignModelLink(
        project_id="water-project",
        revision_id="design-model-rev-1",
        content_sha256="c" * 64,
        parent_authority_kind="STANDALONE_DESIGN_GEOMETRY",
        parent_authority_revision_id="standalone-root-1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
    )
    asset = _asset(asset_id="water-geometry", display_name="Water bottle").with_source_links(
        raw_scan_links=(),
        scan_master_link=None,
        design_model_links=(design_model,),
        preferred_design_model_revision_id=design_model.revision_id,
    )
    store = _library(library_root, assets=(asset,))
    artwork = SkuArtworkPresentationReference(
        label_zone_id="zone-water-front",
        label_zone_design_model_revision_id="design-model-rev-1",
        label_zone_brep_revision_id="brep-rev-1",
        label_zone_brep_geometry_sha256="a" * 64,
        artwork_revision_id="art-rev-1",
        artwork_content_sha256="b" * 64,
        mapping_revision_id="mapping-rev-1",
        assignment_revision_id="assignment-rev-1",
        variant_id="front-primary",
    )
    requested_revisions: list[tuple[str, str]] = []

    def accepted_artwork(asset_id: str, revision_id: str):
        requested_revisions.append((asset_id, revision_id))
        return (artwork,)

    service = PackagingLibraryBrowserService(
        store,
        library_root,
        sku_artwork_references_provider=accepted_artwork,
    )
    summary = service.list_assets()[0]
    before = store.snapshot()
    asset_revision = before.assets[0].revision_id
    created = service.create_sku_from_asset(
        summary,
        sku_id="water-500-red",
        display_name="Water 500 mL · Red Label",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(artwork,),
        expected_state_revision=before.state_revision,
        actor_id="operator-1",
        reason="Create a red label SKU from the shared geometry",
    )

    sku = created.skus[0]
    assert sku.packaging_asset_id == asset.asset_id
    assert sku.packaging_asset_revision_id == asset_revision
    assert sku.preferred_design_model_link == design_model
    assert sku.artwork_references == (artwork,)
    assert not {"supplier", "base_material", "nominal_volume"}.intersection(sku.as_dict())
    assert created.assets == before.assets
    assert requested_revisions == [(asset.asset_id, asset_revision)]
    assert store.validate() == created
    shared = service.create_sku_from_asset(
        summary,
        sku_id="water-500-blue",
        display_name="Water 500 mL · Blue Label",
        status=PackagingSkuStatus.DRAFT,
        artwork_references=(),
        expected_state_revision=created.state_revision,
        actor_id="operator-1",
        reason="Create a second SKU sharing the same geometry",
    )
    assert {item.packaging_asset_id for item in shared.skus} == {asset.asset_id}
    assert {item.packaging_asset_revision_id for item in shared.skus} == {asset_revision}
    assert shared.assets == before.assets
    assert requested_revisions == [(asset.asset_id, asset_revision)] * 2
    assert any(
        item.record_type == "SKU" and item.record_id == "water-500-red"
        for item in service.asset_detail(service.list_assets()[0]).related_records
    )
    view = PackagingLibraryBrowserView(service)
    view.item_view.setCurrentRow(0)
    assert "Water 500 mL · Red Label" in view.detail_text.toPlainText()
    view.close()
    app.processEvents()


def test_create_sku_dialog_cancel_is_noop_and_save_validates_identity(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    app = create_application(["packlab-library-create-sku-dialog-test"])
    library_root = tmp_path / "library"
    store = _library(library_root)
    service = PackagingLibraryBrowserService(store, library_root)
    summary = service.list_assets()[0]
    before = store.snapshot()
    dialog = CreatePackagingSkuDialog(
        service,
        summary,
        expected_state_revision=before.state_revision,
        preview=service.render_preview(service.asset_detail(summary)),
    )
    assert summary.asset_id in dialog.source_identity.text()
    assert summary.revision_id in dialog.source_identity.text()
    assert "Source field provenance stays with the Packaging Asset" in dialog.source_identity.text()
    assert all(
        f"{field}: {classification}" in dialog.source_identity.text()
        for field, classification in summary.field_provenance
    )
    dialog.reject()
    assert store.snapshot() == before

    dialog = CreatePackagingSkuDialog(
        service,
        summary,
        expected_state_revision=before.state_revision,
        preview=service.render_preview(service.asset_detail(summary)),
    )
    dialog.sku_id_field.setText("water-500-blue")
    dialog.display_name_field.setText("Water 500 mL Blue")
    dialog.findChild(QPushButton, "packlab.library.create-sku.save").click()
    assert dialog.created_sku is not None, dialog.error_label.text()
    assert dialog.created_sku.sku_id == "water-500-blue"
    assert store.snapshot().events[-1].operation_type == "SKU_CREATE"
    assert store.snapshot().assets == before.assets
    dialog.close()

    duplicate_dialog = CreatePackagingSkuDialog(
        service,
        summary,
        expected_state_revision=store.snapshot().state_revision,
        preview=service.render_preview(service.asset_detail(summary)),
    )
    duplicate_dialog.sku_id_field.setText("water-500-blue")
    duplicate_dialog.display_name_field.setText("Duplicate SKU identity")
    duplicate_dialog.findChild(QPushButton, "packlab.library.create-sku.save").click()
    assert duplicate_dialog.created_sku is None
    assert "sku_id_already_exists" in duplicate_dialog.error_label.text()
    assert len(store.snapshot().skus) == 1
    duplicate_dialog.close()
    app.processEvents()


def test_create_sku_rejects_stale_accepted_artwork_before_audit_commit(
    tmp_path: Path,
) -> None:
    library_root = tmp_path / "library"
    store = _library(library_root)
    accepted = SkuArtworkPresentationReference(
        label_zone_id="zone-water-front",
        label_zone_design_model_revision_id="model-rev-1",
        label_zone_brep_revision_id="brep-rev-1",
        label_zone_brep_geometry_sha256="a" * 64,
        artwork_revision_id="art-rev-current",
        artwork_content_sha256="b" * 64,
        mapping_revision_id="mapping-rev-current",
        assignment_revision_id="assignment-rev-current",
        variant_id="front-primary",
    )
    stale = SkuArtworkPresentationReference(
        label_zone_id="zone-water-front",
        label_zone_design_model_revision_id="model-rev-1",
        label_zone_brep_revision_id="brep-rev-1",
        label_zone_brep_geometry_sha256="a" * 64,
        artwork_revision_id="art-rev-old",
        artwork_content_sha256="c" * 64,
        mapping_revision_id="mapping-rev-old",
        assignment_revision_id="assignment-rev-old",
        variant_id="front-primary",
    )
    service = PackagingLibraryBrowserService(
        store,
        library_root,
        sku_artwork_references_provider=lambda _asset_id, _revision_id: (accepted,),
    )
    summary = service.list_assets()[0]
    before = store.snapshot()
    with pytest.raises(PackagingLibraryBrowserError, match="artwork_reference_stale"):
        service.create_sku_from_asset(
            summary,
            sku_id="water-500-stale-art",
            display_name="Water with stale artwork",
            status=PackagingSkuStatus.ACTIVE,
            artwork_references=(stale,),
            expected_state_revision=before.state_revision,
            actor_id="operator-1",
            reason="Reject stale artwork assignment",
        )
    assert store.snapshot() == before
