from __future__ import annotations

import json
from dataclasses import replace

import pytest
from test_cad_brep import _inputs

from packlab_core.cad_adapter import probe_cad_runtime
from packlab_core.cad_brep import revolve_design_model_to_brep
from packlab_core.reconstruction import ScaleState
from packlab_core.technical_drawing_title_block import (
    DrawingTitleBlockError,
    build_technical_drawing_title_block,
)


def _source(scale_state: ScaleState, parent_mode: str):
    model, profile, operation = _inputs(scale_state, parent_mode)
    return model, revolve_design_model_to_brep(model, profile, operation)


@pytest.mark.parametrize(
    ("scale_state", "parent_mode", "expected_parent", "unit", "disclaimer_part"),
    [
        (
            ScaleState.RELATIVE,
            "captured",
            "CAPTURED_SCAN_MASTER",
            "reconstruction_units",
            "reconstruction-relative",
        ),
        (
            ScaleState.METRIC_UNVERIFIED,
            "standalone",
            "STANDALONE_DESIGN_GEOMETRY",
            "mm_unverified",
            "unverified against the physical benchmark",
        ),
    ],
)
def test_title_block_pins_authority_units_versions_and_disclaimer(
    scale_state: ScaleState,
    parent_mode: str,
    expected_parent: str,
    unit: str,
    disclaimer_part: str,
) -> None:
    model, representation = _source(scale_state, parent_mode)
    diagnostics = probe_cad_runtime()

    title = build_technical_drawing_title_block(
        model,
        representation,
        diagnostics,
        generated_view_ids=("FRONT", "SIDE", "TOP"),
        generated_at_utc="2026-10-04T12:00:00Z",
    )
    document = title.as_dict()

    assert document["contract"] == "packlab.technical-drawing-title-block.v1"
    assert document["package"]["project_id"] == model.project_id
    assert document["package"]["family"] == model.package_family.value
    assert document["source"]["design_model_revision_id"] == model.revision_id
    assert document["source"]["cad_representation_revision_id"] == representation.revision_id
    assert document["source"]["parent_authority"]["kind"] == expected_parent
    assert document["units"]["coordinate_unit"] == unit
    assert (
        document["software_versions"]["python_cad_binding"]["package"]
        == diagnostics.binding_package
    )
    assert (
        document["software_versions"]["python_cad_binding"]["version"]
        == diagnostics.binding_version
    )
    assert document["software_versions"]["occt_kernel"] == diagnostics.kernel_version
    assert document["generated_views"] == ["FRONT", "SIDE", "TOP"]
    assert disclaimer_part in document["authority_disclaimer"]
    assert "mold" in document["authority_disclaimer"]
    assert "manufacturing" in document["authority_disclaimer"]
    assert "approval" in document["authority_disclaimer"]
    assert document["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert document["mold_use_authorized"] is False
    assert document["certification_claimed"] is False


def test_core_revision_is_deterministic_and_timestamp_is_presentation_only() -> None:
    model, representation = _source(ScaleState.METRIC_UNVERIFIED, "standalone")
    diagnostics = probe_cad_runtime()
    first = build_technical_drawing_title_block(
        model,
        representation,
        diagnostics,
        generated_view_ids=("FRONT", "SIDE", "TOP"),
        generated_at_utc="2026-10-04T12:00:00Z",
    )
    second = build_technical_drawing_title_block(
        model,
        representation,
        diagnostics,
        generated_view_ids=("FRONT", "SIDE", "TOP"),
        generated_at_utc="2026-10-04T13:00:00Z",
    )

    assert first.revision_id == second.revision_id
    assert first.drawing_revision_id == second.drawing_revision_id
    assert first.as_dict()["presentation_metadata"] != second.as_dict()["presentation_metadata"]


def test_title_block_contains_no_machine_identity_or_ambient_path() -> None:
    model, representation = _source(ScaleState.RELATIVE, "standalone")
    title = build_technical_drawing_title_block(
        model,
        representation,
        probe_cad_runtime(),
        generated_view_ids=("FRONT",),
    )
    serialized = json.dumps(title.as_dict(), sort_keys=True)

    assert title.as_dict()["machine_identity_included"] is False
    assert title.as_dict()["ambient_paths_included"] is False
    assert "C:\\" not in serialized
    assert "\\\\Users\\\\" not in serialized
    assert "platform_machine" not in serialized
    assert "sekip" not in serialized.casefold()


def test_unobserved_versions_invalid_views_and_stale_sources_reject() -> None:
    model, representation = _source(ScaleState.RELATIVE, "standalone")
    diagnostics = probe_cad_runtime()

    with pytest.raises(DrawingTitleBlockError, match="software_versions_unobserved"):
        build_technical_drawing_title_block(
            model,
            representation,
            replace(diagnostics, kernel_version_status="UNAVAILABLE"),
            generated_view_ids=("FRONT",),
        )
    with pytest.raises(DrawingTitleBlockError, match="generated_views_invalid"):
        build_technical_drawing_title_block(
            model,
            representation,
            diagnostics,
            generated_view_ids=("FRONT", "FRONT"),
        )
    other_model, _ = _source(ScaleState.METRIC_UNVERIFIED, "standalone")
    with pytest.raises(DrawingTitleBlockError, match="source_authority_mismatch"):
        build_technical_drawing_title_block(
            other_model,
            representation,
            diagnostics,
            generated_view_ids=("FRONT",),
        )
