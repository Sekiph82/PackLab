"""Standalone parametric handle cut, ruled loft and long STEP part names (PL-0459 core fixes)."""

from __future__ import annotations

import math

import pytest

pytest.importorskip("OCP")

from OCP.BRepClass3d import BRepClass3d_SolidClassifier  # noqa: E402
from OCP.gp import gp_Pnt  # noqa: E402
from OCP.TopAbs import TopAbs_IN, TopAbs_OUT  # noqa: E402

from packlab_core.cad_adapter import _shape_for_handle, cad_shape_precise_bounds  # noqa: E402
from packlab_core.cad_boolean import (  # noqa: E402
    PARAMETRIC_HANDLE_OPENING_PREFIX,
    CadBooleanError,
    cut_parametric_handle_opening,
)
from packlab_core.cad_brep import loft_design_model_to_brep  # noqa: E402
from packlab_core.cad_step_export import export_design_model_step  # noqa: E402
from packlab_core.cross_section import SectionPoint, create_cross_section  # noqa: E402
from packlab_core.design_model import (  # noqa: E402
    DesignModelFeatureReference,
    DesignModelParameter,
    FeatureKind,
    PackageFamily,
    ParameterType,
    create_standalone_design_model_revision,
    stable_feature_id,
)
from packlab_core.design_model_binding import (  # noqa: E402
    StandaloneDesignGeometrySourceKind,
    create_standalone_design_geometry_root,
)
from packlab_core.design_operations import LoftSectionInput, create_loft_operation  # noqa: E402
from packlab_core.reconstruction import ScaleState  # noqa: E402

CREATED = "2026-11-21T00:00:00Z"


def _feature(kind: FeatureKind, key: str) -> DesignModelFeatureReference:
    return DesignModelFeatureReference(stable_feature_id("block", kind, key), "block", kind, key)


def _block(
    *,
    widths: tuple[float, ...],
    heights: tuple[float, ...],
    handle: bool = True,
    body_is_opening: bool = False,
):
    """Rectangular loft centred on x = y = 0 (40 deep) with an optional handle opening."""
    root = create_standalone_design_geometry_root(
        project_id="0d6b5b12-18f4-4e8a-9d0d-62fe7116212a",
        source_kind=StandaloneDesignGeometrySourceKind.USER_AUTHORED_NOMINAL_DIMENSIONS,
        source_provenance_id="test:block",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        unit_provenance_id="test:mm",
        actor_id="tester",
        reason="Synthetic block.",
        created_at_utc=CREATED,
    )
    sections_features = tuple(
        _feature(FeatureKind.BODY, f"s{index}") for index in range(len(widths))
    )
    opening = _feature(FeatureKind.HANDLE_OPENING, "opening")
    parameters = (
        DesignModelParameter(
            PARAMETRIC_HANDLE_OPENING_PREFIX + opening.feature_id,
            {
                "body_feature_id": (
                    opening.feature_id if body_is_opening else sections_features[0].feature_id
                ),
                "profile_xz": [[-10.0, 60.0], [10.0, 60.0], [10.0, 80.0], [-10.0, 80.0]],
            },
            ParameterType.OBJECT,
        ),
    )
    model = create_standalone_design_model_revision(
        root,
        package_family=PackageFamily.JERRYCAN,
        parameters=parameters if handle else (),
        features=(*sections_features, opening) if handle else sections_features,
        actor_id="tester",
        reason="Synthetic block.",
        created_at_utc=CREATED,
    )
    previous = None
    inputs = []
    for feature, width, z in zip(sections_features, widths, heights, strict=True):
        points = tuple(
            SectionPoint(x, y)
            for x, y in (
                (-width / 2, -20.0),
                (width / 2, -20.0),
                (width / 2, 20.0),
                (-width / 2, 20.0),
            )
        )
        section = create_cross_section("block", points, previous_section_id=previous)
        previous = section.section_id
        inputs.append(LoftSectionInput(feature.feature_id, section, z))
    operation = create_loft_operation(model, tuple(inputs))
    return model, tuple(inputs), operation, opening.feature_id


def test_ruled_loft_stays_inside_the_section_envelope() -> None:
    model, inputs, operation, _ = _block(
        widths=(100.0, 100.0, 60.0, 60.0), heights=(0.0, 70.0, 75.0, 100.0), handle=False
    )
    smooth = loft_design_model_to_brep(model, inputs, operation)
    ruled = loft_design_model_to_brep(model, inputs, operation, ruled=True)
    assert ruled.geometry_sha256 != smooth.geometry_sha256
    x0, y0, z0, x1, y1, z1 = cad_shape_precise_bounds(ruled.shape_handle)
    assert (x0, x1) == pytest.approx((-50.0, 50.0), abs=1e-6)
    assert (y0, y1, z0, z1) == pytest.approx((-20.0, 20.0, 0.0, 100.0), abs=1e-6)
    sx0, _sy0, _sz0, sx1, _sy1, _sz1 = cad_shape_precise_bounds(smooth.shape_handle)
    assert sx1 - sx0 > 100.0 + 1e-3  # the smooth loft overshoots uneven section spacing


def test_parametric_handle_opening_cuts_through_a_body_centred_on_y_zero(tmp_path) -> None:
    model, inputs, operation, opening = _block(widths=(100.0, 100.0), heights=(0.0, 100.0))
    body = loft_design_model_to_brep(model, inputs, operation, ruled=True)
    result = cut_parametric_handle_opening(model, body, opening)
    assert result.status == "SUCCEEDED" and result.representation is not None
    shape = _shape_for_handle(result.representation.shape_handle)
    # Regression: the tool used to start at the z minimum on the y axis and miss y < 0.
    for y in (-15.0, 0.0, 15.0):
        assert BRepClass3d_SolidClassifier(shape, gp_Pnt(0.0, y, 70.0), 1e-6).State() == TopAbs_OUT
    assert BRepClass3d_SolidClassifier(shape, gp_Pnt(0.0, 0.0, 90.0), 1e-6).State() == TopAbs_IN
    assert result.as_dict()["operation_type"] == "CUT_PARAMETRIC_HANDLE_OPENING_THROUGH_BODY"
    # Long part names wrap in the OCC PRODUCT record; boolean bodies carry enlarged edge
    # tolerances. Both must still pass the exact STEP round trip.
    name = "jerrycan-body-" + "x" * 20
    export = export_design_model_step(
        model, result.representation, tmp_path / "body.step", part_name=name
    )
    assert export.as_dict()["part_name"] == name
    assert math.isclose(
        cad_shape_precise_bounds(result.representation.shape_handle)[5], 100.0, abs_tol=1e-6
    )


def test_parametric_handle_opening_refuses_missing_parameters() -> None:
    model, inputs, operation, _opening = _block(
        widths=(100.0, 100.0), heights=(0.0, 100.0), handle=False
    )
    body = loft_design_model_to_brep(model, inputs, operation, ruled=True)
    with pytest.raises(CadBooleanError, match="feature_missing"):
        cut_parametric_handle_opening(model, body, "packlab-feature:" + "0" * 64)


def test_parametric_handle_opening_is_refused_for_captured_models() -> None:
    from tests.core.test_cad_brep import _inputs

    from packlab_core.cad_brep import revolve_design_model_to_brep

    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED, "captured")
    body = revolve_design_model_to_brep(model, profile, operation)
    with pytest.raises(CadBooleanError, match="requires_standalone_design_geometry"):
        cut_parametric_handle_opening(model, body, model.features[0].feature_id)


def test_parametric_handle_opening_requires_a_body_feature_parent() -> None:
    model, inputs, operation, opening = _block(
        widths=(100.0, 100.0), heights=(0.0, 100.0), body_is_opening=True
    )
    body = loft_design_model_to_brep(model, inputs, operation, ruled=True)
    with pytest.raises(CadBooleanError, match="parameters_invalid"):
        cut_parametric_handle_opening(model, body, opening)
