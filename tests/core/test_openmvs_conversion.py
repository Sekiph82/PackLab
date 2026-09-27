from __future__ import annotations

import hashlib
import json

import pytest
from test_sparse_export import _payload, _run

from packlab_core.openmvs_conversion import (
    DEFAULT_OPENMVS_SCENE_ASSET_ID,
    OPENMVS_ENGINE_VERSION,
    InvalidOpenMVSConversionBundle,
    OpenMVSSceneConversionPlan,
    UnsupportedOpenMVSConversionOption,
    convert_sparse_export_to_openmvs_scene_plan,
)
from packlab_core.sparse_export import SparseExportArtifact, SparseExportBundle


def _bundle() -> SparseExportBundle:
    from packlab_core.sparse_export import export_sparse_mapping

    return export_sparse_mapping(_run(), _payload())


def _with_manifest(**changes: object) -> SparseExportBundle:
    bundle = _bundle()
    manifest = json.loads(bundle.content("debug_manifest.json"))
    manifest.update(changes)
    artifacts = tuple(
        SparseExportArtifact(
            artifact.name,
            json.dumps(manifest, sort_keys=True, separators=(",", ":"))
            if artifact.name == "debug_manifest.json"
            else artifact.content,
        )
        for artifact in bundle.artifacts
    )
    return SparseExportBundle(artifacts)


def test_valid_bundle_produces_immutable_deterministic_plan() -> None:
    plan = convert_sparse_export_to_openmvs_scene_plan(_bundle())

    assert isinstance(plan, OpenMVSSceneConversionPlan)
    assert plan.openmvs_engine_version == OPENMVS_ENGINE_VERSION
    assert plan.output_scene_asset_id == DEFAULT_OPENMVS_SCENE_ASSET_ID
    assert plan.record_counts.as_dict() == {
        "cameras": 1,
        "images": 2,
        "points3d": 1,
        "tracks": 2,
    }
    assert tuple(item.name for item in plan.input_artifacts) == (
        "cameras.txt",
        "images.txt",
        "points3D.txt",
        "debug_manifest.json",
    )
    assert all(len(item.content_digest) == 64 for item in plan.input_artifacts)
    assert "filesystem materialization" in " ".join(plan.limitations)
    assert "METRIC_VERIFIED" in " ".join(plan.limitations)
    assert ".mvs" not in plan.output_scene_asset_id

    equivalent = convert_sparse_export_to_openmvs_scene_plan(
        SparseExportBundle(tuple(reversed(_bundle().artifacts)))
    )
    assert plan.serialize() == equivalent.serialize()
    assert plan.digest == equivalent.digest
    assert plan.digest == hashlib.sha256(plan.serialize().encode("utf-8")).hexdigest()
    assert "executable_path" not in plan.serialize().lower()

    with pytest.raises((AttributeError, TypeError)):
        plan.output_scene_asset_id = "unsafe"  # type: ignore[misc]
    with pytest.raises(TypeError):
        plan.artifact_digests["new.txt"] = "unsafe"  # type: ignore[index]


@pytest.mark.parametrize(
    "changes",
    [
        {"source_digest": "not-a-digest"},
        {"request_digest": "not-a-digest"},
        {"output_asset_id": "working/private/sparse"},
        {"camera_convention": "unsafe-convention"},
        {"record_counts": {"cameras": 2, "images": 2, "points3d": 1, "tracks": 2}},
        {"limitations": ["filesystem materialization"]},
        {"engine": {"id": "openmvs", "version": "2.4.0"}},
    ],
)
def test_manifest_integrity_and_authority_mismatches_fail_closed(
    changes: dict[str, object],
) -> None:
    with pytest.raises((InvalidOpenMVSConversionBundle, UnsupportedOpenMVSConversionOption)):
        convert_sparse_export_to_openmvs_scene_plan(_with_manifest(**changes))


def test_nonfinite_manifest_metadata_and_unsafe_output_fail_closed() -> None:
    bundle = _bundle()
    manifest = json.loads(bundle.content("debug_manifest.json"))
    manifest["record_counts"]["tracks"] = float("nan")
    invalid_manifest = tuple(
        SparseExportArtifact(
            artifact.name,
            json.dumps(manifest, allow_nan=True)
            if artifact.name == "debug_manifest.json"
            else artifact.content,
        )
        for artifact in bundle.artifacts
    )
    with pytest.raises(InvalidOpenMVSConversionBundle):
        convert_sparse_export_to_openmvs_scene_plan(SparseExportBundle(invalid_manifest))

    for output_id in (
        "/private/scene",
        "C:/private/scene",
        "working/../scene",
        "working/private/scene",
    ):
        with pytest.raises(InvalidOpenMVSConversionBundle):
            convert_sparse_export_to_openmvs_scene_plan(bundle, output_scene_asset_id=output_id)


def test_artifact_content_counts_and_artifact_set_are_explicitly_validated() -> None:
    bundle = _bundle()
    altered = tuple(
        SparseExportArtifact(
            artifact.name,
            artifact.content.replace(
                "1 1 0 0 0 0 0 1 7 working/images/001.jpg",
                "9 1 0 0 0 0 0 1 7 working/images/001.jpg",
            )
            if artifact.name == "images.txt"
            else artifact.content,
        )
        for artifact in bundle.artifacts
    )
    with pytest.raises(InvalidOpenMVSConversionBundle):
        convert_sparse_export_to_openmvs_scene_plan(SparseExportBundle(altered))

    with pytest.raises(ValueError):
        SparseExportBundle(bundle.artifacts + (bundle.artifacts[0],))


def test_caller_controlled_openmvs_options_are_rejected_and_plan_has_no_cli_fields() -> None:
    with pytest.raises(UnsupportedOpenMVSConversionOption):
        convert_sparse_export_to_openmvs_scene_plan(
            _bundle(), openmvs_options={"--input-file": "x"}
        )
    with pytest.raises(UnsupportedOpenMVSConversionOption):
        convert_sparse_export_to_openmvs_scene_plan(_bundle(), openmvs_options={"Scene": "x"})

    plan = convert_sparse_export_to_openmvs_scene_plan(_bundle())
    serialized = plan.serialize()
    assert "--input-file" not in serialized
    assert "executable_path" not in serialized.lower()
    assert "dense" in " ".join(plan.limitations).lower()
    assert "mesh" in " ".join(plan.limitations).lower()
    assert "texture" in " ".join(plan.limitations).lower()
