from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from packlab_core.design_model import (
    DesignModelError,
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_design_model_revision,
    resolve_design_model_feature,
    stable_feature_id,
)
from packlab_core.design_model_binding import bind_design_model_parent
from packlab_core.geometry_adapter import TriangleMeshData
from packlab_core.reconstruction import ScaleState
from packlab_core.scan_master import ScanMasterRevision, mesh_sha256

PROJECT = "bd6b5b12-18f4-4e8a-9d0d-62fe7116212a"
MESH = TriangleMeshData(
    ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
    ((0, 1, 2),),
)


def _parent(scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED):
    revision_id = f"scan-master:{hashlib.sha256(b'sm-1').hexdigest()}"
    scan_master = ScanMasterRevision(
        revision_id,
        PROJECT,
        MESH,
        {
            "scan_master_revision_id": revision_id,
            "project_id": PROJECT,
            "authority_class": "SCAN_MASTER",
            "output_geometry_sha256": mesh_sha256(MESH),
            "reconstruction_revision_id": "reconstruction-r1",
            "scale_state": scale_state.value,
            "scale_provenance_id": "scale-provenance:r1",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
            "mold_use_authorized": False,
        },
    )
    return bind_design_model_parent(
        scan_master,
        actor_id="operator-1",
        reason="Initial exact Scan Master selection.",
        created_at_utc="2026-10-03T11:00:00Z",
    )


def _model(parameters: tuple[DesignModelParameter, ...] = ()):
    return create_design_model_revision(
        _parent(),
        package_family=PackageFamily.BOTTLE,
        parameters=parameters,
        features=(
            DesignModelFeatureReference(
                stable_feature_id("container", FeatureKind.BODY, "primary-shell"),
                "container",
                FeatureKind.BODY,
                "primary-shell",
            ),
        ),
        actor_id="operator-1",
        reason="Initial parameter graph.",
        created_at_utc="2026-10-03T12:00:00Z",
    )


def test_graph_identity_is_deterministic_and_parent_is_pinned() -> None:
    parameter = DesignModelParameter("overall-height", 240.0, ParameterType.NUMBER, "mm_unverified")
    first = _model((parameter,))
    repeat = _model((parameter,))
    assert first.revision_id == repeat.revision_id
    assert first.fitted_to_scan_master_revision_id == _parent().fitted_to_scan_master_revision_id
    assert first.parent_binding_revision_id == _parent().revision_id
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.coordinate_unit == "mm_unverified"


def test_parameter_nodes_are_unique_typed_immutable_and_json_ready() -> None:
    with pytest.raises(DesignModelError, match="parameter_value_type_mismatch"):
        DesignModelParameter("height", True, ParameterType.NUMBER)
    with pytest.raises(DesignModelError, match="parameter_number_must_be_finite"):
        DesignModelParameter("height", float("nan"), ParameterType.NUMBER)
    with pytest.raises(DesignModelError, match="parameter_unit_unauthorized"):
        DesignModelParameter("height", 20.0, ParameterType.NUMBER, "mm")
    params = (
        DesignModelParameter("height", 20.0, ParameterType.NUMBER, "mm_unverified"),
        DesignModelParameter("height", 30.0, ParameterType.NUMBER, "mm_unverified"),
    )
    with pytest.raises(DesignModelError, match="parameter_id_duplicate"):
        _model(params)
    nested = DesignModelParameter(
        "metadata", {"empty": {}, "labels": ["front", "back"]}, ParameterType.OBJECT
    )
    serialized = _model((nested,)).as_dict()
    encoded = json.dumps(serialized, sort_keys=True, allow_nan=False)
    assert '"empty": {}' in encoded
    assert "triangle" not in encoded.lower()
    assert "mesh" not in encoded.lower()


def test_parent_scale_semantics_and_physical_validation_deferral_are_preserved() -> None:
    relative = create_design_model_revision(
        _parent(ScaleState.RELATIVE),
        package_family=PackageFamily.JAR,
        actor_id="operator-1",
        reason="Relative-scale model.",
        created_at_utc="2026-10-03T12:00:00Z",
    )
    assert relative.coordinate_unit == "reconstruction_units"
    assert relative.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert relative.mold_use_authorized is False
    with pytest.raises(DesignModelError, match="design_model_coordinate_unit_mismatch"):
        replace(relative, coordinate_unit="mm")
    with pytest.raises(DesignModelError, match="design_model_scale_state_unauthorized"):
        replace(relative, scale_state=ScaleState.METRIC_VERIFIED)


def test_edit_creates_distinct_revision_and_preserves_parent_ancestry() -> None:
    original = _model((DesignModelParameter("height", 20.0, ParameterType.NUMBER),))
    edited = create_design_model_revision(
        _parent(),
        package_family=PackageFamily.BOTTLE,
        parameters=(DesignModelParameter("height", 25.0, ParameterType.NUMBER),),
        features=original.features,
        actor_id="operator-2",
        reason="Height edit.",
        created_at_utc="2026-10-03T13:00:00Z",
        previous_revision_id=original.revision_id,
    )
    assert edited.revision_id != original.revision_id
    assert edited.previous_revision_id == original.revision_id
    assert edited.parent_binding_revision_id == original.parent_binding_revision_id
    assert original.parameters[0].value == 20.0


def test_stable_feature_ids_survive_parameter_edits_and_serialize_semantically() -> None:
    body = DesignModelFeatureReference(
        stable_feature_id("container", FeatureKind.BODY, "primary-shell"),
        "container",
        FeatureKind.BODY,
        "primary-shell",
    )
    first = _model((DesignModelParameter("height", 20.0, ParameterType.NUMBER),))
    edited = create_design_model_revision(
        _parent(),
        package_family=PackageFamily.BOTTLE,
        parameters=(DesignModelParameter("height", 25.0, ParameterType.NUMBER),),
        features=(body,),
        actor_id="operator-2",
        reason="Height edit.",
        created_at_utc="2026-10-03T13:00:00Z",
        previous_revision_id=first.revision_id,
    )
    assert resolve_design_model_feature(first, body.feature_id) == body
    assert resolve_design_model_feature(edited, body.feature_id).feature_id == body.feature_id
    assert body.as_dict() == {
        "feature_id": body.feature_id,
        "component_id": "container",
        "feature_kind": "body",
        "semantic_key": "primary-shell",
    }
    with pytest.raises(DesignModelError, match="feature_id_semantic_mismatch"):
        DesignModelFeatureReference("mesh-index:42", "container", FeatureKind.BODY, "primary-shell")
    with pytest.raises(DesignModelError, match="feature_id_duplicate"):
        create_design_model_revision(
            _parent(),
            package_family=PackageFamily.BOTTLE,
            features=(body, body),
            actor_id="operator-2",
            reason="Duplicate feature rejection.",
            created_at_utc="2026-10-03T13:30:00Z",
        )


@pytest.mark.parametrize(
    "kind",
    [
        FeatureKind.BODY,
        FeatureKind.BASE,
        FeatureKind.SHOULDER,
        FeatureKind.NECK,
        FeatureKind.FINISH,
        FeatureKind.CAP,
    ],
)
def test_all_package_feature_kinds_use_semantic_ids(kind: FeatureKind) -> None:
    feature = DesignModelFeatureReference(
        stable_feature_id("container", kind, "primary"), "container", kind, "primary"
    )
    assert feature.feature_id == stable_feature_id("container", kind, "primary")


def test_deleted_or_replaced_feature_reference_fails_without_retargeting() -> None:
    old = DesignModelFeatureReference(
        stable_feature_id("container", FeatureKind.CAP, "closure-a"),
        "container",
        FeatureKind.CAP,
        "closure-a",
    )
    replacement = DesignModelFeatureReference(
        stable_feature_id("container", FeatureKind.CAP, "closure-b"),
        "container",
        FeatureKind.CAP,
        "closure-b",
    )
    revision = create_design_model_revision(
        _parent(),
        package_family=PackageFamily.BOTTLE,
        features=(replacement,),
        actor_id="operator-2",
        reason="Replace cap component.",
        created_at_utc="2026-10-03T14:00:00Z",
    )
    with pytest.raises(DesignModelError, match="feature_reference_stale_or_deleted"):
        resolve_design_model_feature(revision, old.feature_id)
