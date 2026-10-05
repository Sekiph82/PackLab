from __future__ import annotations

import hashlib
import json

import pytest
from tests.core.test_component_visual_assignments import _library
from tests.core.test_label_zone import COMPONENT_ID, _model

from packlab_core.component_visual_assignments import (
    create_geometry_material_assignment,
    remove_geometry_material_assignment,
)
from packlab_core.pbr_visual_parameters import (
    PbrVisualParametersError,
    create_normal_detail_reference,
    create_pbr_visual_parameter_revision,
)


def _assignment(label: str = "pbr-visual"):
    model = _model(label=label)
    assignment = create_geometry_material_assignment(
        model, COMPONENT_ID, _library(), "material-hdpe"
    )
    return model, assignment


def _pbr(assignment, **overrides: object):
    values: dict[str, object] = {
        "base_color_rgb": (0.2, 0.4, 0.6),
        "roughness_factor": 0.35,
        "transmission_factor": 0.0,
        "opacity_factor": 1.0,
        "ior": 1.5,
    }
    values.update(overrides)
    return create_pbr_visual_parameter_revision(assignment, **values)  # type: ignore[arg-type]


def test_pbr_values_bind_to_exact_model_component_and_material_assignment() -> None:
    model, assignment = _assignment()
    before = model.as_dict()
    parameters = _pbr(assignment)

    assert parameters.source_design_model_revision_id == model.revision_id
    assert parameters.component_id == COMPONENT_ID
    assert parameters.source_geometry_material_assignment_revision_id == assignment.revision_id
    assert parameters.source_material_library_revision_id == assignment.material_library_revision_id
    assert parameters.source_material_id == assignment.material_id
    assert model.as_dict() == before


@pytest.mark.parametrize(
    ("opacity", "transmission", "alpha_mode"),
    [(1.0, 0.0, "OPAQUE"), (0.4, 0.0, "BLEND"), (0.0, 0.0, "BLEND"), (1.0, 0.85, "OPAQUE")],
)
def test_opacity_and_transmission_policy_is_explicit_and_coherent(
    opacity: float, transmission: float, alpha_mode: str
) -> None:
    _, assignment = _assignment(f"pbr-policy-{opacity}-{transmission}")

    result = _pbr(assignment, opacity_factor=opacity, transmission_factor=transmission)

    assert result.opacity_factor == opacity
    assert result.transmission_factor == transmission
    assert result.alpha_mode == alpha_mode


def test_fractional_opacity_and_transmission_cannot_be_combined() -> None:
    _, assignment = _assignment("pbr-policy-conflict")
    with pytest.raises(PbrVisualParametersError, match="opacity_transmission_policy_conflict"):
        _pbr(assignment, opacity_factor=0.5, transmission_factor=0.2)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("base_color_rgb", (-0.01, 0.5, 0.5), "base_color_invalid"),
        ("base_color_rgb", (0.1, float("nan"), 0.5), "base_color_invalid"),
        ("base_color_rgb", (0.1, 0.5), "base_color_invalid"),
        ("roughness_factor", -0.01, "roughness_invalid"),
        ("roughness_factor", float("inf"), "roughness_invalid"),
        ("transmission_factor", 1.01, "transmission_invalid"),
        ("transmission_factor", float("nan"), "transmission_invalid"),
        ("opacity_factor", -0.1, "opacity_invalid"),
        ("opacity_factor", float("inf"), "opacity_invalid"),
        ("ior", 0.99, "ior_out_of_bounds"),
        ("ior", 3.01, "ior_out_of_bounds"),
        ("ior", float("nan"), "ior_out_of_bounds"),
        ("ior", True, "ior_out_of_bounds"),
    ],
)
def test_pbr_numeric_parameters_are_bounded_finite_and_not_booleans(
    field: str, value: object, message: str
) -> None:
    _, assignment = _assignment(f"pbr-invalid-{field}-{message}")
    with pytest.raises(PbrVisualParametersError, match=message):
        _pbr(assignment, **{field: value})


def test_ior_inclusive_bounds_and_visual_only_disclaimer() -> None:
    _, assignment = _assignment("pbr-ior-boundaries")
    lower = _pbr(assignment, ior=1.0)
    upper = _pbr(assignment, ior=3.0)

    value = lower.as_dict()
    assert lower.ior == 1.0
    assert upper.ior == 3.0
    assert value["authority_semantics"] == "NON_CERTIFIED_VISUAL_REFERENCE"
    assert value["ior_semantics"] == "RENDER_PARAMETER_NOT_MEASURED_REFRACTIVE_INDEX"
    assert value["values_are_measured_material_properties"] is False
    assert value["optical_properties_verified"] is False
    assert value["material_certified"] is False
    assert value["regulatory_approval"] is False
    assert value["changes_geometry"] is False
    json.dumps(value, sort_keys=True, allow_nan=False)


def test_normal_detail_reference_pins_digest_and_render_only_metadata() -> None:
    _, assignment = _assignment("pbr-normal-detail")
    digest = hashlib.sha256(b"normal-map-fixture").hexdigest()
    normal = create_normal_detail_reference("normal-asset:revision-1", digest, strength_factor=1.25)
    parameters = _pbr(assignment, normal_detail=normal)
    serialized = parameters.as_dict()
    normal_data = serialized["normal_detail"]

    assert normal_data["texture_asset_revision_id"] == "normal-asset:revision-1"
    assert normal_data["texture_sha256"] == digest
    assert normal_data["strength_factor"] == 1.25
    assert normal_data["coordinate_frame"] == "TANGENT_SPACE"
    assert normal_data["changes_geometry"] is False
    assert normal_data["measured_surface_normal_inferred"] is False
    assert "private" not in json.dumps(serialized).casefold()


@pytest.mark.parametrize(
    ("asset_id", "digest", "strength", "frame", "message"),
    [
        ("C:\\private\\normal.png", "a" * 64, 1.0, "TANGENT_SPACE", "reference_invalid"),
        ("normal-asset:1", None, 1.0, "TANGENT_SPACE", "reference_invalid"),
        ("normal-asset:1", "z" * 64, 1.0, "TANGENT_SPACE", "reference_invalid"),
        ("normal-asset:1", "a" * 64, 2.01, "TANGENT_SPACE", "strength_invalid"),
        ("normal-asset:1", "a" * 64, 1.0, "WORLD", "reference_invalid"),
    ],
)
def test_invalid_normal_detail_reference_metadata_rejects(
    asset_id: str, digest: str, strength: float, frame: str, message: str
) -> None:
    with pytest.raises(PbrVisualParametersError, match=message):
        create_normal_detail_reference(
            asset_id, digest, strength_factor=strength, coordinate_frame=frame
        )


def test_pbr_revision_is_deterministic_and_tracks_parameter_changes() -> None:
    _, assignment = _assignment("pbr-deterministic")
    first = _pbr(assignment, base_color_rgb=(0, 0.5, 1), roughness_factor=0)
    repeated = _pbr(assignment, base_color_rgb=(0.0, 0.5, 1.0), roughness_factor=0.0)
    changed = _pbr(assignment, base_color_rgb=(0.1, 0.5, 1), roughness_factor=0)

    assert first == repeated
    assert first.revision_id == repeated.revision_id
    assert first.revision_id != changed.revision_id


def test_removed_geometry_material_assignment_cannot_receive_pbr_parameters() -> None:
    _, assignment = _assignment("pbr-removed-material")
    removed = remove_geometry_material_assignment(assignment)
    with pytest.raises(
        PbrVisualParametersError, match="active_geometry_material_assignment_required"
    ):
        _pbr(removed)
