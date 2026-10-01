from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from packlab_core.manual_mask_correction import (
    ManualMaskCorrectionError,
    ManualMaskCorrectionService,
    ManualMaskEdit,
    ManualMaskEditAction,
)
from packlab_core.segmentation import (
    CoordinateTransform,
    InvalidMaskArtifact,
    MaskArtifact,
    MaskRaster,
    PromptEvidence,
    PromptKind,
    SegmentationProvenance,
)


def _parent(values: tuple[bool, ...], width: int, height: int) -> MaskArtifact:
    raster = MaskRaster(width, height, values)
    return MaskArtifact(
        artifact_id="raw-mask",
        source_image_asset_id="raw/images/synthetic.png",
        source_digest=hashlib.sha256(b"public synthetic image").hexdigest(),
        source_width=width,
        source_height=height,
        mask_asset_id="working/masks/raw/rev-1.mask",
        mask_digest=raster.digest,
        mask_width=width,
        mask_height=height,
        transform=CoordinateTransform(width, height, width, height),
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
        mask_revision="raw-rev-1",
        created_at="2026-10-01T00:00:00Z",
        post_processing_version="none:raw-model-output",
        raster=raster,
    )


def _edit(x: int, y: int, action: ManualMaskEditAction) -> ManualMaskEdit:
    return ManualMaskEdit(x, y, action)


def _correct(
    parent: MaskArtifact,
    operations: tuple[ManualMaskEdit, ...],
    *,
    editor_id: str = "operator:fixture",
    created_at: str = "2026-10-02T00:00:00Z",
) -> MaskArtifact:
    return ManualMaskCorrectionService().correct(
        parent,
        editor_id=editor_id,
        operations=operations,
        created_at=created_at,
    )


def test_paint_erase_is_domain_only_deterministic_and_preserves_parent() -> None:
    parent = _parent((False, True, False, True), 2, 2)
    before = parent.as_dict()
    before_raster = parent.raster
    operations = (
        _edit(0, 0, ManualMaskEditAction.PAINT),
        _edit(1, 0, ManualMaskEditAction.ERASE),
    )

    child = _correct(parent, operations)
    repeat = _correct(parent, operations, created_at="2026-10-03T00:00:00Z")

    assert child.raster == MaskRaster(2, 2, (True, False, False, True))
    assert child.mask_digest == child.raster.digest
    assert child.mask_revision == repeat.mask_revision
    assert child.artifact_id == repeat.artifact_id
    assert child.created_at != repeat.created_at
    assert child.mask_revision.startswith("manual:")
    assert child.parent_mask_revision == parent.mask_revision
    assert child.source_image_asset_id == parent.source_image_asset_id
    assert child.source_digest == parent.source_digest
    assert child.transform == parent.transform
    assert child.provenance == parent.provenance
    assert parent.as_dict() == before
    assert parent.raster is before_raster


def test_ordered_operations_use_last_edit_for_repeated_pixel() -> None:
    parent = _parent((False,), 1, 1)
    edits = (_edit(0, 0, ManualMaskEditAction.PAINT), _edit(0, 0, ManualMaskEditAction.ERASE))
    with pytest.raises(ManualMaskCorrectionError, match="no-op"):
        _correct(parent, edits)
    reversed_child = _correct(parent, tuple(reversed(edits)))
    assert reversed_child.raster == MaskRaster(1, 1, (True,))


@pytest.mark.parametrize(
    "operation",
    [
        pytest.param(
            lambda: ManualMaskEdit(True, 0, ManualMaskEditAction.PAINT), id="bool-coordinate"
        ),
        pytest.param(
            lambda: ManualMaskEdit(0.5, 0, ManualMaskEditAction.PAINT), id="float-coordinate"
        ),
        pytest.param(lambda: ManualMaskEdit(0, 0, "fill"), id="unsupported-action"),
    ],
)
def test_malformed_edit_rejected(operation) -> None:
    with pytest.raises(ManualMaskCorrectionError):
        operation()


def test_out_of_bounds_noop_empty_and_implicit_editor_rejected() -> None:
    parent = _parent((False, False), 2, 1)
    with pytest.raises(ManualMaskCorrectionError, match="out of bounds"):
        _correct(parent, (_edit(2, 0, ManualMaskEditAction.PAINT),))
    with pytest.raises(ManualMaskCorrectionError, match="at least one"):
        _correct(parent, ())
    with pytest.raises(ManualMaskCorrectionError, match="no-op"):
        _correct(parent, (_edit(0, 0, ManualMaskEditAction.ERASE),))
    with pytest.raises(ManualMaskCorrectionError, match="editor_id"):
        _correct(parent, (_edit(0, 0, ManualMaskEditAction.PAINT),), editor_id="")
    with pytest.raises(ManualMaskCorrectionError, match="editor_id"):
        _correct(
            parent, (_edit(0, 0, ManualMaskEditAction.PAINT),), editor_id="operator@example.com"
        )


def test_digest_mismatch_rejected_before_correction() -> None:
    parent = _parent((False, False), 2, 1)
    mismatched = replace(parent, raster=MaskRaster(2, 1, (True, False)))
    with pytest.raises(InvalidMaskArtifact, match="digest"):
        _correct(mismatched, (_edit(1, 0, ManualMaskEditAction.PAINT),))


def test_editor_evidence_and_ancestry_append_across_repeated_corrections() -> None:
    parent = _parent((False, False), 2, 1)
    first = _correct(parent, (_edit(0, 0, ManualMaskEditAction.PAINT),))
    second = _correct(first, (_edit(1, 0, ManualMaskEditAction.PAINT),))

    assert first.manual_edit_evidence["editor_id"] == "operator:fixture"  # type: ignore[index]
    assert first.manual_edit_ancestry == (first.manual_edit_ancestry[0],)
    assert second.manual_edit_ancestry[:1] == first.manual_edit_ancestry
    assert len(second.manual_edit_ancestry) == 2
    assert second.manual_edit_evidence["parent_digest"] == first.mask_digest  # type: ignore[index]
    assert "manual_edit_evidence" in second.as_dict()


def test_studio_view_cancel_is_session_only_and_submit_delegates(monkeypatch) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    from packlab_studio.app import create_application
    from packlab_studio.mask_correction import MaskCorrectionView

    app = create_application(["packlab-mask-correction-test"])
    parent = _parent((False, False), 2, 1)

    class RecordingService:
        def __init__(self) -> None:
            self.calls = []

        def correct(self, parent, *, editor_id, operations, created_at):
            self.calls.append((parent, editor_id, operations, created_at))
            return ManualMaskCorrectionService().correct(
                parent,
                editor_id=editor_id,
                operations=operations,
                created_at=created_at,
            )

    service = RecordingService()
    view = MaskCorrectionView(correction_service=service)  # type: ignore[arg-type]
    children = []
    view.child_created.connect(children.append)
    view.begin(parent, editor_id="operator:fixture", created_at="2026-10-02T00:00:00Z")
    view.add_pixel_edit(0, 0)
    view.cancel()
    assert service.calls == []
    assert children == []

    view.begin(parent, editor_id="operator:fixture", created_at="2026-10-02T00:00:00Z")
    view.add_pixel_edit(0, 0)
    view.undo()
    assert view.status.text() == "0 unsubmitted pixel edit(s)"
    view.add_pixel_edit(1, 0)
    view.submit()
    assert len(service.calls) == 1
    assert service.calls[0][0] is parent
    assert children[0].raster == MaskRaster(2, 1, (False, True))
    assert children[0].manual_edit_evidence["revision_identity_sha256"] in children[0].mask_revision  # type: ignore[index]
    view.close()
    app.processEvents()
