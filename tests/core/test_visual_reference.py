from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.visual_reference import (
    AI_VISUAL_REFERENCE_AUTHORITY,
    AI_VISUAL_REFERENCE_CAVEAT,
    ConditioningInput,
    VisualReferenceError,
    VisualReferenceProvenance,
    VisualReferenceRecord,
    content_sha256,
    reject_visual_reference_promotion,
)

IMAGE = "1" * 64
MASK = "2" * 64
ARTIFACT = "3" * 64


def _record(*, settings: dict[str, object] | None = None) -> VisualReferenceRecord:
    provenance = VisualReferenceProvenance.create(
        generator="adapter/example",
        model="example-model",
        checkpoint="example-checkpoint",
        version="1.2.3",
        conditioning=(ConditioningInput(IMAGE, MASK),),
        seed=0,
        settings=settings or {"quality": "preview"},
        checkpoint_sha256=ARTIFACT,
    )
    return VisualReferenceRecord("visual-reference:one", ARTIFACT, provenance)


def test_record_is_generated_labelled_and_serializes_complete_provenance() -> None:
    record = _record()

    payload = record.as_dict()

    assert record.generated is True
    assert record.authority_class == AI_VISUAL_REFERENCE_AUTHORITY
    assert record.caveat == AI_VISUAL_REFERENCE_CAVEAT
    assert payload["generated"] is True
    assert payload["authority_class"] == "AI_VISUAL_REFERENCE"
    assert payload["caveat"] == AI_VISUAL_REFERENCE_CAVEAT
    assert payload["provenance"]["conditioning"] == [{"image_sha256": IMAGE, "mask_sha256": MASK}]
    assert payload["provenance"]["seed"] == 0
    assert payload["provenance"]["settings"] == {"quality": "preview"}
    assert "points" not in payload and "vertices" not in payload


def test_provenance_settings_are_canonical_and_reject_non_finite_values() -> None:
    with pytest.raises(VisualReferenceError, match="settings_not_json_safe"):
        VisualReferenceProvenance.create(
            generator="g",
            model="m",
            checkpoint="c",
            version="v",
            conditioning=(ConditioningInput(IMAGE),),
            seed=1,
            settings={"value": float("nan")},
        )

    record = _record(settings={"b": 2, "a": 1})
    assert record.provenance.settings_json == json.dumps(
        {"a": 1, "b": 2}, separators=(",", ":"), sort_keys=True
    )


@pytest.mark.parametrize("digest", ["", "A" * 64, "g" * 64, "0" * 63])
def test_invalid_content_digest_is_rejected(digest: str) -> None:
    with pytest.raises(VisualReferenceError):
        ConditioningInput(digest)


def test_visual_reference_can_never_be_promoted_to_authoritative_geometry() -> None:
    with pytest.raises(VisualReferenceError, match="cannot_be_promoted"):
        reject_visual_reference_promotion(_record())


def test_content_digest_does_not_store_input_bytes() -> None:
    assert content_sha256(b"visual artifact") == hashlib.sha256(b"visual artifact").hexdigest()
