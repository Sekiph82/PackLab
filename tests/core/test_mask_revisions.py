from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.manual_mask_correction import (
    ManualMaskCorrectionService,
    ManualMaskEdit,
    ManualMaskEditAction,
)
from packlab_core.mask_revisions import (
    MaskRevisionError,
    MaskRevisionService,
    StaleMaskGeometryError,
)
from packlab_core.segmentation import (
    CoordinateTransform,
    MaskArtifact,
    MaskRaster,
    PromptEvidence,
    PromptKind,
    SegmentationProvenance,
)

CREATED_AT = "2026-10-02T00:00:00Z"
SOURCE_BYTES = b"synthetic raw capture source fixture"
SOURCE_DIGEST = hashlib.sha256(SOURCE_BYTES).hexdigest()


def _mask(artifact_id: str, revision: str, values: tuple[bool, ...]) -> MaskArtifact:
    raster = MaskRaster(2, 1, values)
    return MaskArtifact(
        artifact_id=artifact_id,
        source_image_asset_id=f"raw/images/{artifact_id}.png",
        source_digest=SOURCE_DIGEST,
        source_width=2,
        source_height=1,
        mask_asset_id=f"working/masks/{revision}.mask",
        mask_digest=raster.digest,
        mask_width=2,
        mask_height=1,
        transform=CoordinateTransform(2, 1, 2, 1),
        provenance=SegmentationProvenance(
            "fixture-backend",
            "1",
            "fixture-model",
            "1",
            "fixture-checkpoint",
            hashlib.sha256(b"fixture-checkpoint").hexdigest(),
            "fixture-runtime",
            "1",
            "tests/fixtures/licenses/fixture.txt",
        ),
        prompt=PromptEvidence(PromptKind.AUTOMATIC),
        mask_revision=revision,
        created_at=CREATED_AT,
        post_processing_version="none:raw-model-output",
        raster=raster,
    )


def _manual_child(parent: MaskArtifact, *, created_at: str = CREATED_AT) -> MaskArtifact:
    return ManualMaskCorrectionService().correct(
        parent,
        editor_id="operator:fixture",
        operations=(ManualMaskEdit(0, 0, ManualMaskEditAction.PAINT),),
        created_at=created_at,
    )


def test_initial_revision_identity_is_ordered_canonical_and_timestamp_independent() -> None:
    first_mask = _mask("object-a", "mask-a-r1", (False, False))
    second_mask = _mask("object-b", "mask-b-r1", (True, False))
    first = MaskRevisionService().publish_initial(
        project_id="project-1",
        source_revision="capture-r1",
        masks=(first_mask, second_mask),
        created_at="2026-10-02T00:00:00Z",
    )
    repeated = MaskRevisionService().publish_initial(
        project_id="project-1",
        source_revision="capture-r1",
        masks=(
            replace(second_mask, created_at="2026-10-03T00:00:00Z"),
            replace(first_mask, created_at="2026-10-03T00:00:00Z"),
        ),
        created_at="2026-10-03T00:00:00Z",
    )

    assert first.revision_id == repeated.revision_id
    assert first.revision_digest == repeated.revision_digest
    assert first.created_at != repeated.created_at
    assert tuple(mask.artifact_id for mask in first.masks) == ("object-a", "object-b")
    assert first.revision_id.startswith("maskset:")


def test_manual_replacement_publishes_new_child_and_preserves_other_masks() -> None:
    retained = _mask("object-a", "mask-a-r1", (False, False))
    replaced = _mask("object-b", "mask-b-r1", (False, False))
    service = MaskRevisionService()
    first = service.publish_initial(
        project_id="project-1",
        source_revision="capture-r1",
        masks=(retained, replaced),
        created_at=CREATED_AT,
    )
    child_mask = _manual_child(replaced)
    child = service.publish_child(
        first,
        replacements={replaced.artifact_id: child_mask},
        created_at=CREATED_AT,
    )

    assert child.revision_id != first.revision_id
    assert child.parent_revision_id == first.revision_id
    assert child.revision_digest != first.revision_digest
    assert tuple(mask.artifact_id for mask in child.masks) == tuple(
        mask.artifact_id for mask in first.masks if mask.artifact_id != replaced.artifact_id
    ) + (child_mask.artifact_id,)
    assert first.masks[1] is replaced
    assert service.history("project-1", "capture-r1") == (first, child)
    assert service.current("project-1", "capture-r1") is child
    assert child_mask.parent_mask_revision == replaced.mask_revision
    assert child_mask.manual_edit_ancestry
    assert hashlib.sha256(SOURCE_BYTES).hexdigest() == SOURCE_DIGEST

    next_child_mask = ManualMaskCorrectionService().correct(
        child_mask,
        editor_id="operator:fixture",
        operations=(ManualMaskEdit(1, 0, ManualMaskEditAction.PAINT),),
        created_at=CREATED_AT,
    )
    next_child = service.publish_child(
        child,
        replacements={child_mask.artifact_id: next_child_mask},
        created_at=CREATED_AT,
    )
    assert next_child_mask.manual_edit_ancestry[:1] == child_mask.manual_edit_ancestry
    assert len(next_child_mask.manual_edit_ancestry) == 2
    assert next_child.parent_revision_id == child.revision_id


def test_duplicate_initial_and_duplicate_child_entries_fail_closed() -> None:
    mask = _mask("object-a", "mask-a-r1", (False, False))
    service = MaskRevisionService()
    with pytest.raises(MaskRevisionError, match="at least one"):
        MaskRevisionService().publish_initial(
            project_id="project-empty",
            source_revision="capture-r1",
            masks=(),
            created_at=CREATED_AT,
        )
    first = service.publish_initial(
        project_id="project-1",
        source_revision="capture-r1",
        masks=(mask,),
        created_at=CREATED_AT,
    )
    with pytest.raises(MaskRevisionError, match="initial revision already exists"):
        service.publish_initial(
            project_id="project-1",
            source_revision="capture-r1",
            masks=(mask,),
            created_at=CREATED_AT,
        )
    with pytest.raises(MaskRevisionError, match="duplicate or ambiguous"):
        service.publish_child(
            first,
            additions=(mask,),
            created_at=CREATED_AT,
        )
    duplicate_revision = replace(mask, artifact_id="other-artifact")
    with pytest.raises(MaskRevisionError, match="mask revision IDs"):
        MaskRevisionService().publish_initial(
            project_id="project-duplicate",
            source_revision="capture-r1",
            masks=(mask, duplicate_revision),
            created_at=CREATED_AT,
        )


def test_replacement_requires_parent_identity_lineage_and_preserved_provenance() -> None:
    original = _mask("object-a", "mask-a-r1", (False, False))
    service = MaskRevisionService()
    first = service.publish_initial(
        project_id="project-1",
        source_revision="capture-r1",
        masks=(original,),
        created_at=CREATED_AT,
    )
    no_lineage = replace(
        _mask("object-a-new", "mask-a-r2", (True, False)), parent_mask_revision="mask-a-r1"
    )
    with pytest.raises(MaskRevisionError, match="manual edit provenance"):
        service.publish_child(
            first,
            replacements={original.artifact_id: no_lineage},
            created_at=CREATED_AT,
        )
    forged_parent = replace(first, created_at="2026-10-03T00:00:00Z")
    with pytest.raises(MaskRevisionError, match="parent mask-set revision is not the current head"):
        service.publish_child(
            forged_parent,
            replacements={original.artifact_id: _manual_child(original)},
            created_at=CREATED_AT,
        )
    valid_child = _manual_child(original)
    service.publish_child(
        first,
        replacements={original.artifact_id: valid_child},
        created_at=CREATED_AT,
    )
    with pytest.raises(MaskRevisionError, match="parent mask-set revision is not the current head"):
        service.publish_child(
            first,
            replacements={original.artifact_id: valid_child},
            created_at=CREATED_AT,
        )


def test_geometry_binding_becomes_stale_after_mask_set_revision_changes() -> None:
    original = _mask("object-a", "mask-a-r1", (False, False))
    service = MaskRevisionService()
    first = service.publish_initial(
        project_id="project-1",
        source_revision="capture-r1",
        masks=(original,),
        created_at=CREATED_AT,
    )
    geometry_binding = service.bind_geometry(first)
    service.require_geometry_current(
        geometry_binding,
        project_id="project-1",
        source_revision="capture-r1",
    )
    service.publish_child(
        first,
        replacements={original.artifact_id: _manual_child(original)},
        created_at=CREATED_AT,
    )

    with pytest.raises(StaleMaskGeometryError, match="must be regenerated"):
        service.require_geometry_current(
            geometry_binding,
            project_id="project-1",
            source_revision="capture-r1",
        )
