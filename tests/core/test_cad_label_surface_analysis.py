from __future__ import annotations

import math
import typing

import pytest
from test_cad_brep import _inputs, _model

import packlab_core.cad_label_surface_analysis as surface_analysis
from packlab_core.cad_adapter import (
    _registered_shape_build,
)
from packlab_core.cad_brep import _representation_from_lineage, revolve_design_model_to_brep
from packlab_core.cad_label_surface_analysis import (
    CadLabelSurfaceAnalysisError,
    CadLabelSurfacePolicy,
    analyze_cad_label_surfaces,
)
from packlab_core.reconstruction import ScaleState

if typing.TYPE_CHECKING:
    from OCP.TopoDS import TopoDS_Shape

PROJECT_LABEL = "cad-label-surface-analysis"


def _from_shape(
    shape: TopoDS_Shape,
    *,
    scale_state: ScaleState = ScaleState.METRIC_UNVERIFIED,
    parent_mode: str = "standalone",
    label: str = PROJECT_LABEL,
):
    model = _model(scale_state, parent_mode, label)
    feature = model.features[0]
    operation_id = f"fixture:{label}"
    build = _registered_shape_build(
        model,
        operation_id,
        (feature.feature_id,),
        shape,
        1,
    )
    representation = _representation_from_lineage(
        model,
        operation_id,
        (feature.feature_id,),
        build,
        source_feature_ids=(feature.feature_id,),
    )
    return model, representation


def _box(*, label: str = PROJECT_LABEL):
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox

    return _from_shape(BRepPrimAPI_MakeBox(10.0, 20.0, 30.0).Shape(), label=label)


def test_box_planar_patch_is_low_curvature_advisory_candidate() -> None:
    model, brep = _box()

    result = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 0, 1), 0, 0))

    candidates = [
        item for item in result.candidates if item.advisory_classification == "LABEL_SAFE_CANDIDATE"
    ]
    assert candidates
    assert all(item.surface_type == "GeomAbs_Plane" for item in candidates)
    assert all(item.maximum_absolute_curvature == 0.0 for item in candidates)
    assert all(item.feature_attribution_status == "UNRESOLVED" for item in candidates)
    assert all(item.resolved_feature_id is None for item in candidates)


def test_cylinder_curvature_matches_reciprocal_radius_and_seam_is_flagged() -> None:
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeCylinder

    model, brep = _from_shape(
        BRepPrimAPI_MakeCylinder(5.0, 20.0).Shape(),
        label="cylinder-curvature",
    )
    policy = CadLabelSurfacePolicy((0, 1, 0), 45, 0.21, samples_per_axis=9, maximum_faces=8)

    result = analyze_cad_label_surfaces(model, brep, policy)

    cylindrical = [item for item in result.candidates if item.surface_type == "GeomAbs_Cylinder"]
    assert cylindrical
    assert all(
        item.maximum_absolute_curvature == pytest.approx(0.2, abs=1e-8) for item in cylindrical
    )
    assert any(item.periodic_seam_boundary for item in cylindrical)
    assert any(item.advisory_classification == "LABEL_SAFE_CANDIDATE" for item in cylindrical)


def test_sloped_planar_surface_includes_exact_slope_threshold_boundary() -> None:
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Transform
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
    from OCP.gp import gp_Ax1, gp_Dir, gp_Pnt, gp_Trsf

    rotation = gp_Trsf()
    rotation.SetRotation(gp_Ax1(gp_Pnt(0, 0, 0), gp_Dir(0, 1, 0)), math.pi / 4)
    shape = BRepBuilderAPI_Transform(
        BRepPrimAPI_MakeBox(10, 20, 30).Shape(), rotation, True
    ).Shape()
    model, brep = _from_shape(shape, label="sloped-planar")

    inclusive = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 0, 1), 45, 0))
    below = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 0, 1), 44.9, 0))

    assert any(
        item.advisory_classification == "LABEL_SAFE_CANDIDATE"
        and item.maximum_slope_degrees == pytest.approx(45, abs=1e-7)
        for item in inclusive.candidates
    )
    assert not any(
        item.advisory_classification == "LABEL_SAFE_CANDIDATE" and item.maximum_slope_degrees > 44.9
        for item in below.candidates
    )


def test_high_curvature_sphere_is_rejected_by_curvature_threshold() -> None:
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeSphere

    model, brep = _from_shape(BRepPrimAPI_MakeSphere(1.0).Shape(), label="curved-sphere")

    result = analyze_cad_label_surfaces(
        model,
        brep,
        CadLabelSurfacePolicy((0, 0, 1), 90, 0.5, samples_per_axis=5, maximum_faces=16),
    )

    assert result.candidates
    assert all(item.maximum_absolute_curvature > 0.5 for item in result.candidates)
    assert all(
        item.advisory_classification == "NOT_SAFE_UNDER_POLICY" for item in result.candidates
    )


def test_accepted_ambiguous_revolve_preserves_component_and_null_feature_owner() -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    brep = revolve_design_model_to_brep(model, profile, operation)

    result = analyze_cad_label_surfaces(
        model, brep, CadLabelSurfacePolicy((0, 1, 0), 90, 1, samples_per_axis=4)
    )
    metadata = result.as_dict()

    assert result.component_id == model.features[0].component_id
    assert result.feature_attribution_status == "AMBIGUOUS"
    assert result.candidates
    assert all(item.feature_attribution_status == "AMBIGUOUS" for item in result.candidates)
    assert all(item.resolved_feature_id is None for item in result.candidates)
    expected_ids = {
        item.feature_id for item in model.features if item.feature_id in brep.source_feature_ids
    }
    assert {item.feature_id for item in result.contributing_features} == expected_ids
    assert metadata["sampling"]["face_traversal_index_used_as_identity"] is False
    assert metadata["sampling"]["mesh_or_preview_used_as_authority"] is False
    assert metadata["advisory_only"] is True
    assert metadata["automatic_production_approval"] is False


@pytest.mark.parametrize(
    ("scale_state", "parent_mode", "expected_unit"),
    [
        (ScaleState.RELATIVE, "standalone", "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "standalone", "mm_unverified"),
        (ScaleState.RELATIVE, "captured", "reconstruction_units"),
        (ScaleState.METRIC_UNVERIFIED, "captured", "mm_unverified"),
    ],
)
def test_parent_and_scale_authority_are_preserved(
    scale_state: ScaleState, parent_mode: str, expected_unit: str
) -> None:
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox

    model, brep = _from_shape(
        BRepPrimAPI_MakeBox(10, 10, 10).Shape(),
        scale_state=scale_state,
        parent_mode=parent_mode,
        label=f"{parent_mode}-{scale_state.value}",
    )

    result = analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 0, 1), 0, 0))
    metadata = result.as_dict()

    assert result.scale_state == scale_state.value
    assert result.coordinate_unit == expected_unit
    assert result.parent_kind == model.parent_kind.value
    assert result.parent_authority_revision_id == (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    assert result.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert result.mold_use_authorized is False
    assert all(
        item.coordinate_unit_for_curvature == f"inverse_{expected_unit}"
        for item in result.candidates
    )
    assert metadata["advisory_only"] is True


def test_analysis_is_order_independent_of_transient_face_traversal(monkeypatch) -> None:
    model, brep = _box(label="ordering")
    policy = CadLabelSurfacePolicy((0, 0, 1), 0, 0)
    baseline = analyze_cad_label_surfaces(model, brep, policy)
    original = surface_analysis.sample_cad_surface_regions

    monkeypatch.setattr(
        surface_analysis,
        "sample_cad_surface_regions",
        lambda *args, **kwargs: tuple(reversed(original(*args, **kwargs))),
    )
    reordered = analyze_cad_label_surfaces(model, brep, policy)

    assert reordered.revision_id == baseline.revision_id
    assert reordered.candidates == baseline.candidates


def test_duplicate_geometric_region_signature_fails_closed(monkeypatch) -> None:
    model, brep = _box(label="collision")
    original = surface_analysis.sample_cad_surface_regions

    def duplicate(*args, **kwargs):
        regions = original(*args, **kwargs)
        return (regions[0], regions[0])

    monkeypatch.setattr(surface_analysis, "sample_cad_surface_regions", duplicate)
    with pytest.raises(
        CadLabelSurfaceAnalysisError,
        match="cad_label_analysis_region_signature_collision",
    ):
        analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 0, 1), 90, 100))


def test_invalid_thresholds_and_sampling_bounds_reject() -> None:
    with pytest.raises(CadLabelSurfaceAnalysisError, match="cad_label_target_normal_invalid"):
        CadLabelSurfacePolicy((0, 0, 0), 45, 1)
    with pytest.raises(CadLabelSurfaceAnalysisError, match="cad_label_target_normal_invalid"):
        CadLabelSurfacePolicy((10**10_000, 0, 0), 45, 1)
    with pytest.raises(CadLabelSurfaceAnalysisError, match="cad_label_slope_threshold_invalid"):
        CadLabelSurfacePolicy((0, 0, 1), math.inf, 1)
    with pytest.raises(CadLabelSurfaceAnalysisError, match="cad_label_curvature_threshold_invalid"):
        CadLabelSurfacePolicy((0, 0, 1), 45, -1)
    with pytest.raises(CadLabelSurfaceAnalysisError, match="cad_label_region_work_bound_exceeded"):
        CadLabelSurfacePolicy((0, 0, 1), 45, 1, samples_per_axis=16)


def test_source_model_and_brep_must_match_exactly() -> None:
    from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox

    first, brep = _from_shape(BRepPrimAPI_MakeBox(10, 10, 10).Shape(), label="source-a")
    other, _ = _from_shape(BRepPrimAPI_MakeBox(10, 10, 10).Shape(), label="source-b")

    with pytest.raises(CadLabelSurfaceAnalysisError, match="cad_label_surface_provenance_mismatch"):
        analyze_cad_label_surfaces(other, brep, CadLabelSurfacePolicy((0, 0, 1), 90, 10))
    assert first.revision_id != other.revision_id


def test_analysis_revision_is_deterministic_and_candidate_ids_are_brep_scoped() -> None:
    model, brep = _box(label="identity")
    policy = CadLabelSurfacePolicy((0, 0, 1), 0, 0)

    first = analyze_cad_label_surfaces(model, brep, policy)
    second = analyze_cad_label_surfaces(model, brep, policy)

    assert first.revision_id == second.revision_id
    assert tuple(item.analysis_region_id for item in first.candidates) == tuple(
        sorted(item.analysis_region_id for item in first.candidates)
    )
    assert len({item.analysis_region_id for item in first.candidates}) == len(first.candidates)
    assert all(
        item.analysis_region_id.startswith("cad-analysis-region:") for item in first.candidates
    )
    assert all("face_id" not in item.as_dict() for item in first.candidates)


def test_analysis_does_not_mutate_design_model_or_brep_authority() -> None:
    model, brep = _box(label="immutability")
    model_before = model.as_dict()
    brep_before = brep.as_dict()

    analyze_cad_label_surfaces(model, brep, CadLabelSurfacePolicy((0, 0, 1), 0, 0))

    assert model.as_dict() == model_before
    assert brep.as_dict() == brep_before
