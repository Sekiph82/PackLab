from __future__ import annotations

import json

from PySide6.QtCore import QSize

from packlab_core.visual_reference import (
    ConditioningInput,
    VisualReferenceProvenance,
    VisualReferenceRecord,
)
from packlab_studio.app import create_application
from packlab_studio.viewport import (
    PointCloudGeometry,
    SceneObject,
    SceneObjectKind,
    ViewportService,
)
from packlab_studio.viewport_export import ViewportPreviewExporter


def _record() -> VisualReferenceRecord:
    provenance = VisualReferenceProvenance.create(
        generator="adapter/example",
        model="example-model",
        checkpoint="example-checkpoint",
        version="1.2.3",
        conditioning=(ConditioningInput("1" * 64),),
        seed=0,
        settings={"quality": "preview"},
    )
    return VisualReferenceRecord("generated-reference", "2" * 64, provenance)


def test_ai_visual_reference_visibility_is_independent_and_serialized() -> None:
    service = ViewportService()
    service.add_geometry(
        "captured-scan",
        SceneObjectKind.SCAN_MESH,
        PointCloudGeometry(((0.0, 0.0, 0.0),)),
    )
    service.add_visual_reference(
        _record(),
        PointCloudGeometry(((1.0, 0.0, 0.0),)),
    )

    service.set_visible("generated-reference", False)

    assert service.scene.get("captured-scan").visible is True
    assert service.scene.get("generated-reference").visible is False
    generated = service.scene.get("generated-reference").to_dict()
    assert generated["authority_class"] == "AI_VISUAL_REFERENCE"
    assert generated["generated"] is True
    assert "unseen geometry may be invented" in generated["caveat"].lower()
    assert generated["visual_reference"]["provenance"]["model"] == "example-model"


def test_removing_visual_reference_preserves_captured_scan_object() -> None:
    service = ViewportService()
    scan = service.add_geometry(
        "captured-scan",
        SceneObjectKind.SCAN_MESH,
        PointCloudGeometry(((0.0, 0.0, 0.0),)),
    )
    service.add_visual_reference(_record(), PointCloudGeometry(((1.0, 0.0, 0.0),)))
    original_geometry = scan.geometry

    service.remove_visual_reference("generated-reference")

    assert service.scene.get("captured-scan").geometry is original_geometry
    assert tuple(item.object_id for item in service.scene.objects()) == ("captured-scan",)


def test_generated_status_overlay_is_visible_only_with_reference() -> None:
    from packlab_studio.app import create_application

    create_application(["packlab-visual-reference-test"])
    service = ViewportService()
    baseline = service.render(QSize(240, 160))
    service.scene.add(
        SceneObject(
            "generated-reference",
            SceneObjectKind.AI_VISUAL_REFERENCE,
            visual_reference=_record(),
        )
    )

    labelled = service.render(QSize(240, 160))
    service.set_visible("generated-reference", False)
    hidden = service.render(QSize(240, 160))

    assert labelled != baseline
    assert hidden == baseline


def test_viewport_preview_sidecar_preserves_generated_label_and_visibility(tmp_path) -> None:
    service = ViewportService()
    service.add_visual_reference(
        _record(),
        PointCloudGeometry(((0.0, 0.0, 0.0),)),
    )

    result = ViewportPreviewExporter().export(
        service,
        tmp_path / "visual-reference.png",
        size=QSize(240, 160),
    )

    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    reference = metadata["scene_objects"][0]
    assert reference["authority_class"] == "AI_VISUAL_REFERENCE"
    assert reference["generated"] is True
    assert reference["visible"] is True
    assert "unseen geometry may be invented" in reference["caveat"].lower()
    assert reference["visual_reference"]["provenance"]["checkpoint"] == "example-checkpoint"


def test_viewport_preview_sidecar_redacts_paths_and_credential_values(tmp_path) -> None:
    create_application(["packlab-visual-reference-redaction-test"])
    provenance = VisualReferenceProvenance.create(
        generator="adapter/example",
        model="example-model",
        checkpoint=r"C:\Users\Private User\model.safetensors",
        version="1.2.3",
        conditioning=(ConditioningInput("1" * 64),),
        seed=0,
        settings={
            "quality": "preview",
            "source_path": "/Users/private user/capture.png",
            "auxiliary_note": "cached under /Volumes/Private Volume/packlab/input.jpg",
            "network_note": "mirror //fileserver/share/private/input.png",
            "environment_note": r"cached at %USERPROFILE%\Private User\scan.png",
            "home_environment_note": r"cached at $HOME\Private User\scan.png",
            "home_shortcut_note": "cached at ~/Private User/scan.png",
            "braced_environment_note": "cached at ${HOME}/Private User/scan.png",
            "root_relative_note": r"cached at \Users\Private User\scan.png",
            "api_token": "do-not-export-this-value",
            r"C:\Users\Private User\credential.txt": "key-name-must-not-survive",
        },
    )
    record = VisualReferenceRecord(
        r"C:\Users\private\generated-reference",
        "2" * 64,
        provenance,
    )
    service = ViewportService()
    service.add_visual_reference(record, PointCloudGeometry(((1.0, 0.0, 0.0),)))

    result = ViewportPreviewExporter().export(
        service,
        tmp_path / "redacted-preview.png",
        size=QSize(240, 160),
    )

    serialized = result.metadata_path.read_text(encoding="utf-8")
    metadata = json.loads(serialized)
    assert metadata["paths_redacted"] is True
    assert "C:\\Users\\Private User" not in serialized
    assert "/Users/private user" not in serialized
    assert "/Volumes/Private Volume" not in serialized
    assert "//fileserver/share/private" not in serialized
    assert "%USERPROFILE%" not in serialized
    assert "$HOME" not in serialized
    assert "~/Private User" not in serialized
    assert "${HOME}" not in serialized
    assert r"\Users\Private User" not in serialized
    assert "do-not-export-this-value" not in serialized
    assert "key-name-must-not-survive" not in serialized
    reference = metadata["scene_objects"][0]["visual_reference"]
    assert reference["provenance"]["checkpoint"] == "[REDACTED]"
    assert "api_token" not in reference["provenance"]["settings"]
    assert reference["provenance"]["settings"]["[REDACTED]_KEY"] == "[REDACTED]"
