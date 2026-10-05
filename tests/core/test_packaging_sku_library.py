from __future__ import annotations

import json

import pytest
from tests.core.test_label_zone_placement import _zone
from tests.core.test_packaging_asset import _asset

from packlab_core.label_artwork import (
    create_label_artwork_assignment,
    ingest_label_artwork,
    map_label_artwork_to_zone,
)
from packlab_core.label_zone import LabelZoneKind
from packlab_core.label_zone_placement import create_label_zone_placement_revision
from packlab_core.packaging_sku_library import (
    PackagingSkuCatalog,
    PackagingSkuError,
    PackagingSkuRevision,
    PackagingSkuStatus,
    SkuArtworkPresentationReference,
)


def _artwork_reference(color: str, variant_id: str) -> SkuArtworkPresentationReference:
    _, _, zone = _zone(LabelZoneKind.FRONT)
    placement = create_label_zone_placement_revision(
        zone,
        zone.boundary,
        actor_id="operator-1",
        reason="Pin SKU artwork to an accepted Label Zone placement.",
        created_at_utc="2026-10-04T14:00:00Z",
    )
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" '
        f'viewBox="0 0 200 100"><rect width="200" height="100" fill="{color}"/></svg>'
    ).encode()
    artwork = ingest_label_artwork(svg)
    mapping = map_label_artwork_to_zone(artwork, placement, fit_mode="CONTAIN")
    assignment = create_label_artwork_assignment(mapping, placement, variant_id=variant_id)
    return SkuArtworkPresentationReference.from_accepted_assignment(
        zone, artwork, mapping, assignment
    )


def test_two_skus_share_exact_geometry_and_keep_distinct_artwork_authority() -> None:
    asset = _asset()
    front_red = _artwork_reference("red", "front-red")
    front_blue = _artwork_reference("blue", "front-blue")
    first = PackagingSkuRevision.create(
        asset,
        sku_id="water-500-red",
        display_name="500 mL Red Label",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(front_red,),
    )
    second = PackagingSkuRevision.create(
        asset,
        sku_id="water-500-blue",
        display_name="500 mL Blue Label",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(front_blue,),
    )
    catalog = (
        PackagingSkuCatalog()
        .with_revision(
            first,
            assets=(asset,),
            artwork_references=(front_red, front_blue),
        )
        .with_revision(
            second,
            assets=(asset,),
            artwork_references=(front_red, front_blue),
        )
    )

    shared_geometry_skus = catalog.skus_for_geometry(asset.asset_id)
    assert tuple(item.sku_id for item in shared_geometry_skus) == (
        "water-500-blue",
        "water-500-red",
    )
    assert {item.packaging_asset_revision_id for item in shared_geometry_skus} == {
        asset.revision_id
    }
    assert front_red.artwork_revision_id != front_blue.artwork_revision_id
    assert front_red.artwork_content_sha256 != front_blue.artwork_content_sha256
    assert first.artwork_references != second.artwork_references
    serialized = json.dumps(catalog.as_dict(), sort_keys=True)
    assert '"artwork_bytes_included": false' in serialized
    assert "<svg" not in serialized
    assert '"geometry_copied": false' in serialized


def test_catalog_retains_deterministic_history_and_updates_current_pointer() -> None:
    asset = _asset()
    first_art = _artwork_reference("red", "front-primary")
    second_art = _artwork_reference("blue", "front-primary")
    first = PackagingSkuRevision.create(
        asset,
        sku_id="water-500",
        display_name="500 mL Water",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(first_art,),
    )
    second = PackagingSkuRevision.create(
        asset,
        sku_id="water-500",
        display_name="500 mL Water Blue",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(second_art,),
    )
    catalog = PackagingSkuCatalog().with_revision(
        first,
        assets=(asset,),
        artwork_references=(first_art, second_art),
    )
    revised = catalog.with_revision(
        second,
        assets=(asset,),
        artwork_references=(first_art, second_art),
    )

    assert len(revised.revisions) == 2
    assert catalog.revisions == (first,)
    assert revised.skus_for_geometry(asset.asset_id, include_history=True) == tuple(
        sorted((first, second), key=lambda item: item.revision_id)
    )
    assert revised.skus_for_geometry(asset.asset_id) == (second,)
    assert (
        revised.revision_id
        == PackagingSkuCatalog(revised.revisions, revised.current_revision_ids).revision_id
    )


def test_stale_duplicate_and_malformed_references_fail_closed() -> None:
    asset = _asset()
    reference = _artwork_reference("red", "front-primary")
    sku = PackagingSkuRevision.create(
        asset,
        sku_id="water-500",
        display_name="500 mL Water",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(reference,),
    )
    with pytest.raises(PackagingSkuError, match="asset_target_stale_or_missing"):
        sku.validate_targets((), (reference,))
    with pytest.raises(PackagingSkuError, match="artwork_target_stale_or_missing"):
        sku.validate_targets((asset,), ())
    with pytest.raises(PackagingSkuError, match="artwork_reference_duplicate"):
        PackagingSkuRevision.create(
            asset,
            sku_id="water-500",
            display_name="500 mL Water",
            status=PackagingSkuStatus.ACTIVE,
            artwork_references=(reference, reference),
        )
    with pytest.raises(PackagingSkuError, match="label_zone_id_invalid"):
        SkuArtworkPresentationReference(
            label_zone_id="../local/path",
            label_zone_design_model_revision_id="model-rev-1",
            label_zone_brep_revision_id="brep-rev-1",
            label_zone_brep_geometry_sha256="0" * 64,
        )
    with pytest.raises(PackagingSkuError, match="presentation_reference_incomplete"):
        SkuArtworkPresentationReference(
            label_zone_id="zone-1",
            label_zone_design_model_revision_id="model-rev-1",
            label_zone_brep_revision_id="brep-rev-1",
            label_zone_brep_geometry_sha256="0" * 64,
        )


def test_catalog_rejects_geometry_identity_change_and_duplicate_revision() -> None:
    asset = _asset()
    reference = _artwork_reference("red", "front-primary")
    sku = PackagingSkuRevision.create(
        asset,
        sku_id="water-500",
        display_name="500 mL Water",
        status=PackagingSkuStatus.ACTIVE,
        artwork_references=(reference,),
    )
    catalog = PackagingSkuCatalog().with_revision(
        sku,
        assets=(asset,),
        artwork_references=(reference,),
    )
    with pytest.raises(PackagingSkuError, match="revision_duplicate"):
        catalog.with_revision(sku, assets=(asset,), artwork_references=(reference,))

    other_geometry = _asset(asset_id="other-pack-001")
    changed = PackagingSkuRevision.create(
        other_geometry,
        sku_id="water-500",
        display_name="500 mL Water",
        status=PackagingSkuStatus.ACTIVE,
    )
    with pytest.raises(PackagingSkuError, match="geometry_identity_change_forbidden"):
        catalog.with_revision(changed, assets=(other_geometry,), artwork_references=())
