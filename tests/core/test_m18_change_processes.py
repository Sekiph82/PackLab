"""PL-0415 / PL-0416 / PL-0417 synthetic dry-runs of the library change processes.

Every ID and digest here is synthetic. The tests exercise the real Packaging Asset and SKU
revision contracts that the process documents rely on; they do not represent a real
supplier, artwork, scan or Kenya package.
"""

from __future__ import annotations

import hashlib

import pytest
from tests.core.test_packaging_asset import _asset
from tests.core.test_packaging_sku_library import _artwork_reference

from packlab_core.packaging_asset import (
    DesignModelLink,
    FieldProvenance,
    PackagingAsset,
    ProvenanceClass,
    RawScanLink,
    ScanMasterLink,
)
from packlab_core.packaging_sku_library import (
    PackagingSkuCatalog,
    PackagingSkuError,
    PackagingSkuRevision,
    PackagingSkuStatus,
)
from packlab_core.reconstruction import ScaleState


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def _geometry(scan: str) -> dict[str, object]:
    master = ScanMasterLink(
        project_id="SYNTHETIC-TEST-PKG-0001",
        revision_id=f"scan-master-{scan}",
        geometry_sha256=_sha(f"geometry-{scan}"),
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id=f"scale-{scan}",
    )
    model = DesignModelLink(
        project_id="SYNTHETIC-TEST-PKG-0001",
        revision_id=f"design-{scan}",
        content_sha256=_sha(f"design-{scan}"),
        parent_authority_kind="CAPTURED_SCAN_MASTER",
        parent_authority_revision_id=master.revision_id,
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scan_master_revision_id=master.revision_id,
        scan_master_geometry_sha256=master.geometry_sha256,
    )
    raw = RawScanLink("SYNTHETIC-TEST-PKG-0001", f"raw-{scan}", _sha(f"raw-{scan}"))
    return {
        "raw_scan_links": (raw,),
        "scan_master_link": master,
        "design_model_links": (model,),
        "preferred_design_model_revision_id": model.revision_id,
    }


def _baseline() -> PackagingAsset:
    return _asset().with_source_links(**_geometry("scan-1"))  # type: ignore[arg-type]


def _supplier_change(asset: PackagingAsset) -> PackagingAsset:
    evidence = "SYNTHETIC-supplier-change-request-0002"
    return asset.with_field_update(
        "supplier_id",
        "supplier-002",
        FieldProvenance("supplier_id", ProvenanceClass.SUPPLIER_FACT, source_reference_id=evidence),
    ).with_field_update(
        "supplier_name",
        "Second Example Supplier",
        FieldProvenance(
            "supplier_name", ProvenanceClass.SUPPLIER_FACT, source_reference_id=evidence
        ),
    )


def _sku(asset: PackagingAsset, artwork: tuple = ()) -> PackagingSkuRevision:
    return PackagingSkuRevision.create(
        asset,
        sku_id="SYNTHETIC-TEST-SKU-0001",
        display_name="Synthetic 500 mL SKU",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=artwork,
    )


def test_pl0415_supplier_change_is_a_new_traceable_revision_reusing_verified_geometry() -> None:
    original = _baseline()
    changed = _supplier_change(original)
    assert changed.asset_id == original.asset_id
    assert changed.revision_id != original.revision_id
    assert changed.scan_master_link == original.scan_master_link
    assert changed.design_model_links == original.design_model_links
    assert original.as_dict()["supplier"]["supplier_id"] == "supplier-001"  # old stays readable
    assert changed.as_dict()["supplier_certification_inferred"] is False
    assert changed.as_dict()["physical_accuracy_verified"] is False

    old_sku = _sku(original)
    catalog = PackagingSkuCatalog().with_revision(
        old_sku, assets=(original,), artwork_references=()
    )
    migrated = _sku(changed)
    catalog = catalog.with_revision(migrated, assets=(original, changed), artwork_references=())
    history = catalog.skus_for_geometry(original.asset_id, include_history=True)
    assert {item.packaging_asset_revision_id for item in history} == {
        original.revision_id,
        changed.revision_id,
    }
    assert catalog.skus_for_geometry(original.asset_id)[0].revision_id == migrated.revision_id
    old_sku.validate_targets((original, changed), ())
    with pytest.raises(PackagingSkuError, match="stale_or_missing"):
        old_sku.validate_targets((changed,), ())  # deleting the old revision breaks lineage


def test_pl0416_artwork_only_change_reuses_the_exact_geometry_revision() -> None:
    asset = _baseline()
    red, blue = _artwork_reference("red", "front-red"), _artwork_reference("blue", "front-blue")
    before = _sku(asset, (red,))
    after = _sku(asset, (blue,))
    catalog = (
        PackagingSkuCatalog()
        .with_revision(before, assets=(asset,), artwork_references=(red, blue))
        .with_revision(after, assets=(asset,), artwork_references=(red, blue))
    )
    assert before.revision_id != after.revision_id
    assert before.packaging_asset_revision_id == after.packaging_asset_revision_id
    assert asset.revision_id == _baseline().revision_id  # asset untouched by the artwork change
    assert after.as_dict()["geometry_reference"]["geometry_copied"] is False
    assert catalog.skus_for_geometry(asset.asset_id)[0].artwork_references == (blue,)
    assert len(catalog.skus_for_geometry(asset.asset_id, include_history=True)) == 2
    with pytest.raises(PackagingSkuError, match="artwork_target_stale_or_missing"):
        after.validate_targets((asset,), (red,))


def test_pl0417_geometry_change_needs_a_new_scan_revision_and_explicit_sku_migration() -> None:
    current = _baseline()
    rescanned = current.with_source_links(**_geometry("scan-2"))  # type: ignore[arg-type]
    assert rescanned.revision_id != current.revision_id
    assert rescanned.scan_master_link != current.scan_master_link
    assert current.scan_master_link is not None
    assert current.scan_master_link.revision_id == "scan-master-scan-1"  # old geometry retained
    for link in (rescanned.scan_master_link, *rescanned.design_model_links):
        assert link is not None and link.mold_use_authorized is False

    pinned = _sku(current)
    catalog = PackagingSkuCatalog().with_revision(pinned, assets=(current,), artwork_references=())
    # A new asset revision alone never moves the SKU.
    assert catalog.skus_for_geometry(current.asset_id)[0].packaging_asset_revision_id == (
        current.revision_id
    )
    moved = catalog.with_revision(
        _sku(rescanned), assets=(current, rescanned), artwork_references=()
    )
    assert moved.skus_for_geometry(current.asset_id)[0].packaging_asset_revision_id == (
        rescanned.revision_id
    )

    different_package = _asset(asset_id="kenya-pack-002").with_source_links(  # type: ignore[arg-type]
        **_geometry("scan-3")
    )
    with pytest.raises(PackagingSkuError, match="geometry_identity_change_forbidden"):
        catalog.with_revision(
            _sku(different_package), assets=(current, different_package), artwork_references=()
        )
