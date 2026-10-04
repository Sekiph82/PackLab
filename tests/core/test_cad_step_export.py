from __future__ import annotations

from pathlib import Path

import pytest
from tests.core.test_cad_brep import _inputs

from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.cad_step_export import CadStepExportError, export_design_model_step
from packlab_core.reconstruction import ScaleState


def test_step_export_is_deterministic_named_and_reopens_as_millimetres(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)

    first_path = tmp_path / "first.step"
    second_path = tmp_path / "second.step"
    first = export_design_model_step(model, representation, first_path, part_name="Bottle Body V1")
    second = export_design_model_step(
        model, representation, second_path, part_name="Bottle Body V1"
    )

    assert first_path.read_bytes() == second_path.read_bytes()
    assert (
        Path(str(first_path) + ".json").read_bytes()
        == Path(str(second_path) + ".json").read_bytes()
    )
    assert first.artifact_sha256 == second.artifact_sha256
    assert first.export_id == second.export_id
    assert first.encoded_step_unit == "millimetre"
    assert first.reopened_step_length_units == ("millimetre",)
    assert first.round_trip_validation == second.round_trip_validation
    assert first.round_trip_validation.report_id.startswith("cad-step-roundtrip:")
    assert first.round_trip_validation.numerical_tolerance > 0
    assert first.round_trip_validation.as_dict()["numerical_fidelity_only"] is True
    assert first.round_trip_validation.as_dict()["manufacturing_tolerance_inferred"] is False
    assert first.as_dict()["round_trip_validation"]["physical_accuracy_inferred"] is False
    assert (
        Path(str(first_path) + ".json").read_bytes()
        == Path(str(second_path) + ".json").read_bytes()
    )
    assert "Bottle Body V1" in first_path.read_text(encoding="ascii")
    assert first.source_design_model_revision_id == model.revision_id
    assert first.source_brep_revision_id == representation.revision_id
    assert first.source_brep_geometry_sha256 == representation.geometry_sha256
    assert first.parent_authority_revision_id == representation.parent_authority_revision_id
    assert tuple(item["feature_id"] for item in first.feature_mapping) == tuple(
        feature.feature_id for feature in model.features
    )


def test_relative_design_model_is_rejected_without_creating_a_file(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.RELATIVE)
    representation = revolve_design_model_to_brep(model, profile, operation)
    output = tmp_path / "relative.step"

    with pytest.raises(CadStepExportError, match="mm_unverified_source_required"):
        export_design_model_step(model, representation, output, part_name="Relative Model")

    assert not output.exists()


def test_step_metadata_keeps_physical_and_authority_claims_explicit(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    exported = export_design_model_step(
        model, representation, tmp_path / "bottle.step", part_name="Bottle"
    )
    metadata = exported.as_dict()

    assert exported.scale_state == ScaleState.METRIC_UNVERIFIED.value
    assert exported.coordinate_unit == "mm_unverified"
    assert exported.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert exported.mold_use_authorized is False
    assert metadata["physical_accuracy_inferred"] is False
    assert metadata["mold_or_manufacturing_suitability_inferred"] is False
    assert metadata["scan_master_promoted"] is False
    assert metadata["design_model_replaced"] is False
    assert metadata["cad_brep_replaced"] is False
    assert metadata["timestamp_policy"] == "source_design_model_created_at_utc"


@pytest.mark.parametrize("parent_mode", ("standalone", "captured"))
def test_step_export_preserves_each_explicit_parent_authority(tmp_path, parent_mode: str) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED, parent_mode)
    representation = revolve_design_model_to_brep(model, profile, operation)
    original_model = model.as_dict()
    original_brep_digest = representation.geometry_sha256

    exported = export_design_model_step(
        model,
        representation,
        tmp_path / f"{parent_mode}.step",
        part_name="Bottle",
    )

    assert exported.parent_kind == model.parent_kind.value
    assert exported.parent_authority_revision_id == representation.parent_authority_revision_id
    assert model.as_dict() == original_model
    assert representation.geometry_sha256 == original_brep_digest


def test_step_export_refuses_existing_destination(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)
    output = tmp_path / "existing.step"
    output.write_text("owner data", encoding="utf-8")

    with pytest.raises(CadStepExportError, match="destination_exists"):
        export_design_model_step(model, representation, output, part_name="Bottle")

    assert output.read_text(encoding="utf-8") == "owner data"


def test_step_part_name_is_ascii_and_rejects_controls(tmp_path) -> None:
    model, profile, operation = _inputs(ScaleState.METRIC_UNVERIFIED)
    representation = revolve_design_model_to_brep(model, profile, operation)

    with pytest.raises(CadStepExportError, match="part_name_invalid"):
        export_design_model_step(
            model, representation, tmp_path / "invalid.step", part_name="Bötle"
        )

    assert not (tmp_path / "invalid.step").exists()
