from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.cross_section import circle_section
from packlab_core.design_model import (
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.design_operations import (
    LoftSectionInput,
    create_loft_operation,
    create_revolve_operation,
)
from packlab_core.design_profile import ProfilePoint, create_design_profile
from packlab_core.design_serialization import (
    DesignSerializationError,
    deserialize_design_model,
    serialize_design_model,
)
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _document_parts():
    scan_id = f"scan-master:{hashlib.sha256(b'serialization-parent').hexdigest()}"
    binding = bind_design_model_parent(
        ScanMasterRevision(
            scan_id,
            PROJECT,
            MESH,
            {
                "scan_master_revision_id": scan_id,
                "project_id": PROJECT,
                "authority_class": "SCAN_MASTER",
                "output_geometry_sha256": mesh_sha256(MESH),
                "reconstruction_revision_id": "reconstruction-r1",
                "scale_state": ScaleState.METRIC_UNVERIFIED.value,
                "scale_provenance_id": "scale-r1",
                "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
                "mold_use_authorized": False,
            },
        ),
        actor_id="operator-1",
        reason="Initial selection.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    kinds = (
        (FeatureKind.BODY, "body"),
        (FeatureKind.NECK, "axis"),
        (FeatureKind.BASE, "section-base"),
        (FeatureKind.SHOULDER, "section-top"),
    )
    features = tuple(
        DesignModelFeatureReference(
            stable_feature_id("container", kind, semantic),
            "container",
            kind,
            semantic,
        )
        for kind, semantic in kinds
    )
    model = create_design_model_revision(
        binding,
        package_family=PackageFamily.BOTTLE,
        parameters=(
            DesignModelParameter("overall-height", 100.0, ParameterType.NUMBER, "mm_unverified"),
        ),
        features=features,
        actor_id="operator-1",
        reason="Initial editable model.",
        created_at_utc="2026-10-03T12:30:00Z",
    )
    profile = create_design_profile(
        (ProfilePoint(0.0, 10.0), ProfilePoint(100.0, 10.0)),
        ScaleState.METRIC_UNVERIFIED,
    )
    sections = (
        circle_section("container", 12.0, point_count=16),
        circle_section("container", 8.0, point_count=16),
    )
    operations = (
        create_revolve_operation(
            model,
            profile,
            profile_feature_id=features[0].feature_id,
            axis_feature_id=features[1].feature_id,
        ),
        create_loft_operation(
            model,
            (
                LoftSectionInput(features[2].feature_id, sections[0], 0.0),
                LoftSectionInput(features[3].feature_id, sections[1], 50.0),
            ),
        ),
    )
    return model, (profile,), sections, operations


def test_round_trip_preserves_revision_features_operations_parent_and_units() -> None:
    model, profiles, sections, operations = _document_parts()
    encoded = serialize_design_model(
        model, profiles=profiles, cross_sections=sections, operations=operations
    )
    restored = deserialize_design_model(
        encoded,
        expected_scan_master_revision_id=model.fitted_to_scan_master_revision_id,
        expected_scan_master_geometry_sha256=model.scan_master_geometry_sha256,
        expected_parent_binding_revision_id=model.parent_binding_revision_id,
    )
    assert restored.model == model
    assert restored.profiles == profiles
    assert restored.cross_sections == tuple(sorted(sections, key=lambda item: item.section_id))
    assert restored.operations == tuple(sorted(operations, key=lambda item: item.operation_id))
    assert restored.model.coordinate_unit == "mm_unverified"
    assert restored.model.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert restored.model.mold_use_authorized is False


def test_serialized_bytes_are_canonical_and_exclude_preview_mesh_authority() -> None:
    model, profiles, sections, operations = _document_parts()
    first = serialize_design_model(
        model, profiles=profiles, cross_sections=sections, operations=operations
    )
    assert model.revision_id == (
        "design-model:073ffb34da80cf16b1569f5d7dbc0b69e8fddb68c164edeb374bb37f9c90dcd0"
    )
    assert hashlib.sha256(first).hexdigest() == (
        "c90772fe0630c6c9fc6eb80b3cc563cdd710e2541fe03d67b83a0ef805e92f09"
    )
    repeat = serialize_design_model(
        model,
        profiles=tuple(reversed(profiles)),
        cross_sections=tuple(reversed(sections)),
        operations=tuple(reversed(operations)),
    )
    assert first == repeat
    assert b"preview" not in first.lower()
    assert b"mesh" not in first.lower()
    body = json.loads(first)["body"]
    assert (
        body["model"]["parent"]["scan_master_revision_id"]
        == model.fitted_to_scan_master_revision_id
    )
    assert body["operations"][0]["output_geometry"] is None


def test_duplicate_keys_unsupported_versions_and_digest_tampering_reject() -> None:
    model, profiles, sections, operations = _document_parts()
    encoded = serialize_design_model(
        model, profiles=profiles, cross_sections=sections, operations=operations
    )
    with pytest.raises(DesignSerializationError, match="duplicate_json_key"):
        deserialize_design_model(b'{"body":{},"body":{},"content_sha256":"' + b"0" * 64 + b'"}')
    envelope = json.loads(encoded)
    envelope["body"]["contract"] = "packlab.design-model-document.v99"
    with pytest.raises(DesignSerializationError, match="document_version_unsupported"):
        deserialize_design_model(json.dumps(envelope))
    tampered = json.loads(encoded)
    tampered["body"]["model"]["reason"] = "changed without updating digest"
    with pytest.raises(DesignSerializationError, match="document_digest_mismatch"):
        deserialize_design_model(json.dumps(tampered))


def test_parent_context_and_feature_reference_integrity_fail_closed() -> None:
    model, profiles, sections, operations = _document_parts()
    encoded = serialize_design_model(
        model, profiles=profiles, cross_sections=sections, operations=operations
    )
    with pytest.raises(DesignSerializationError, match="scan_master_parent_revision_stale"):
        deserialize_design_model(encoded, expected_scan_master_revision_id="scan-master:other")
    with pytest.raises(DesignSerializationError, match="scan_master_parent_digest_stale"):
        deserialize_design_model(encoded, expected_scan_master_geometry_sha256="0" * 64)
    broken = operations[0]
    object.__setattr__(
        broken, "parent_feature_ids", ("removed-feature", *broken.parent_feature_ids[1:])
    )
    with pytest.raises(DesignSerializationError, match="operation_feature_reference_stale"):
        serialize_design_model(
            model, profiles=profiles, cross_sections=sections, operations=(broken, operations[1])
        )
