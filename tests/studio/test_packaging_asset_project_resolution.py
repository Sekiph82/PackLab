from __future__ import annotations

from pathlib import Path

from packlab_core.packaging_asset import (
    DesignModelLink,
    FieldProvenance,
    PackagingAsset,
    PackagingFamily,
    ProvenanceClass,
    RawScanLink,
)
from packlab_core.reconstruction import ScaleState
from packlab_studio.packaging_asset_project_resolution import (
    ProjectRootAvailability,
    resolve_packaging_asset_project_roots,
)

PROJECT_A = "a1111111-1111-4111-8111-111111111111"
PROJECT_B = "b2222222-2222-4222-8222-222222222222"
_DIGEST_A = "a" * 64
_DIGEST_B = "b" * 64


def _asset() -> PackagingAsset:
    return PackagingAsset(
        asset_id="kenya-link-test",
        display_name="Linked bottle",
        family=PackagingFamily.BOTTLE,
        field_provenance=(
            FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
            FieldProvenance("family", ProvenanceClass.USER_DECLARED),
        ),
        raw_scan_links=(RawScanLink(PROJECT_A, "capture-1", _DIGEST_A),),
        design_model_links=(
            DesignModelLink(
                project_id=PROJECT_B,
                revision_id="design-model-1",
                content_sha256=_DIGEST_B,
                parent_authority_kind="STANDALONE_DESIGN_GEOMETRY",
                parent_authority_revision_id="standalone-root-1",
                scale_state=ScaleState.METRIC_UNVERIFIED,
            ),
        ),
    )


def test_missing_project_resolution_is_transient_and_preserves_canonical_links() -> None:
    asset = _asset()
    before_json = asset.canonical_json
    before_revision = asset.revision_id
    calls: list[str] = []

    resolved = resolve_packaging_asset_project_roots(
        asset, lambda project_id: calls.append(project_id) or None
    )

    assert calls == [PROJECT_A, PROJECT_B]
    assert tuple(item.project_id for item in resolved) == (PROJECT_A, PROJECT_B)
    assert all(item.availability is ProjectRootAvailability.UNAVAILABLE for item in resolved)
    assert all(item.project_root is None for item in resolved)
    assert asset.canonical_json == before_json
    assert asset.revision_id == before_revision


def test_available_roots_are_runtime_only_and_do_not_rewrite_asset() -> None:
    asset = _asset()
    before_json = asset.canonical_json
    roots = {PROJECT_A: Path("C:/PackLab/ProjectA"), PROJECT_B: Path("D:/PackLab/ProjectB")}

    resolved = resolve_packaging_asset_project_roots(asset, roots.__getitem__)

    assert tuple(item.availability for item in resolved) == (
        ProjectRootAvailability.AVAILABLE,
        ProjectRootAvailability.AVAILABLE,
    )
    assert tuple(item.project_root for item in resolved) == (roots[PROJECT_A], roots[PROJECT_B])
    assert asset.canonical_json == before_json
