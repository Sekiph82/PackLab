from __future__ import annotations

import importlib

import pytest
from tests.core.test_cad_brep import _inputs
from tests.core.test_cad_loft import _loft_inputs

from packlab_core.cad_adapter import _shape_for_handle
from packlab_core.cad_brep import loft_design_model_to_brep, revolve_design_model_to_brep
from packlab_core.cad_step_export import export_design_model_step
from packlab_core.cad_step_roundtrip import (
    CadStepRoundTripError,
    validate_step_export_round_trip,
)
from packlab_core.reconstruction import ScaleState


def test_loft_step_export_round_trip_rechecks_bounds_and_units(tmp_path) -> None:
    model, sections, operation = _loft_inputs()
    representation = loft_design_model_to_brep(model, sections, operation)
    exported = export_design_model_step(
        model, representation, tmp_path / "loft.step", part_name="Loft Body"
    )
    report = exported.round_trip_validation

    assert report.reopened_length_units == ("millimetre",)
    assert report.solid_count == representation.solid_count == 1
    assert report.maximum_bounds_delta <= report.numerical_tolerance
    assert report.source_dimensions == pytest.approx(report.reopened_dimensions, abs=1e-6)
    assert report.tolerance_basis.endswith("not a physical tolerance")


def test_corrupted_step_fails_closed(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    path = tmp_path / "corrupt.step"
    path.write_bytes(b"not a STEP exchange file")

    with pytest.raises(CadStepRoundTripError, match="cad_step_roundtrip_unreadable"):
        validate_step_export_round_trip(path, model, representation, expected_part_name="Bottle")


def test_shell_only_step_fails_closed_for_missing_solid(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    shape = _shape_for_handle(representation.shape_handle)
    top_exp = importlib.import_module("OCP.TopExp")
    top_abs = importlib.import_module("OCP.TopAbs")
    topods = importlib.import_module("OCP.TopoDS")
    step = importlib.import_module("OCP.STEPControl")
    ifselect = importlib.import_module("OCP.IFSelect")
    interface = importlib.import_module("OCP.Interface").Interface_Static
    explorer = top_exp.TopExp_Explorer(shape, top_abs.TopAbs_SHELL)
    shell = topods.TopoDS.Shell_s(explorer.Current())
    path = tmp_path / "shell.step"
    previous_unit = interface.CVal_s("write.step.unit")
    try:
        assert interface.SetCVal_s("write.step.unit", "MM")
        writer = step.STEPControl_Writer()
        assert writer.Transfer(shell, step.STEPControl_AsIs) == ifselect.IFSelect_RetDone
        assert writer.Write(str(path)) == ifselect.IFSelect_RetDone
    finally:
        interface.SetCVal_s("write.step.unit", previous_unit)

    with pytest.raises(CadStepRoundTripError, match="cad_step_roundtrip_solid_count_mismatch"):
        validate_step_export_round_trip(path, model, representation, expected_part_name="Bottle")


def test_part_name_mismatch_and_bounds_drift_fail_closed(tmp_path, monkeypatch) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    exported = export_design_model_step(
        model, representation, tmp_path / "bottle.step", part_name="Bottle"
    )

    with pytest.raises(CadStepRoundTripError, match="cad_step_roundtrip_part_name_mismatch"):
        validate_step_export_round_trip(
            tmp_path / "bottle.step",
            model,
            representation,
            expected_part_name="Other Part",
        )

    import packlab_core.cad_step_roundtrip as roundtrip

    source_bounds = roundtrip.cad_shape_bounds(representation.shape_handle)
    calls = 0

    def drifted_bounds(_handle):
        nonlocal calls
        calls += 1
        if calls == 1:
            return source_bounds
        return (source_bounds[0], source_bounds[1] + 1.0, *source_bounds[2:])

    monkeypatch.setattr(roundtrip, "cad_shape_bounds", drifted_bounds)
    with pytest.raises(CadStepRoundTripError, match="cad_step_roundtrip_bounds_drift_exceeded"):
        validate_step_export_round_trip(
            tmp_path / "bottle.step",
            model,
            representation,
            expected_part_name="Bottle",
        )
    assert exported.round_trip_validation.maximum_bounds_delta <= (
        exported.round_trip_validation.numerical_tolerance
    )
