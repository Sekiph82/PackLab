from __future__ import annotations

import pytest
from test_design_serialization import _document_parts

from packlab_core.design_model import revise_design_model_revision
from packlab_core.design_operations import create_revolve_operation
from packlab_core.design_preview import (
    DesignPreviewError,
    tessellate_design_preview,
)
from packlab_core.reconstruction import ScaleState


def test_revolve_and_loft_preview_meshes_are_deterministic_and_provenance_bound() -> None:
    model, profiles, sections, operations = _document_parts()
    kwargs = {
        "profiles": profiles,
        "cross_sections": sections,
        "operations": operations,
        "chord_tolerance": 0.25,
        "profile_samples": 12,
        "maximum_angular_segments": 64,
    }
    first = tessellate_design_preview(model, **kwargs)
    second = tessellate_design_preview(model, **kwargs)
    assert first == second
    assert len(first) == 2
    revolve = next(item for item in first if len(item.feature_vertex_indices) == 1)
    loft = next(item for item in first if len(item.feature_vertex_indices) == 2)
    assert len(revolve.mesh.vertices) > 0 and len(revolve.mesh.triangles) > 0
    assert len(loft.mesh.vertices) == 32
    assert len(loft.mesh.triangles) == 32
    assert all(
        0 <= index < len(preview.mesh.vertices)
        for preview in first
        for _feature_id, indices in preview.feature_vertex_indices
        for index in indices
    )
    for preview in first:
        metadata = preview.as_dict()
        assert metadata["authority_class"] == "PREVIEW_PROXY"
        assert metadata["disposable"] is True
        assert metadata["scan_master_promoted"] is False
        assert metadata["model_revision_id"] == model.revision_id
        assert metadata["scan_master_revision_id"] == model.fitted_to_scan_master_revision_id
        assert metadata["scan_master_geometry_sha256"] == model.scan_master_geometry_sha256
        assert metadata["scale_state"] == ScaleState.METRIC_UNVERIFIED.value
        assert metadata["coordinate_unit"] == "mm_unverified"
        assert metadata["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
        assert metadata["mold_use_authorized"] is False
        assert "vertices" not in metadata and "triangles" not in metadata


def test_revolve_chord_tolerance_and_work_parameters_are_bounded() -> None:
    model, profiles, sections, operations = _document_parts()
    revolve = next(item for item in operations if item.axis_direction is not None)
    with pytest.raises(DesignPreviewError, match="chord_tolerance_exceeds_work_bound"):
        tessellate_design_preview(
            model,
            profiles=profiles,
            cross_sections=sections,
            operations=(revolve,),
            chord_tolerance=1e-12,
            maximum_angular_segments=8,
        )
    with pytest.raises(DesignPreviewError, match="profile_sample_count_invalid"):
        tessellate_design_preview(
            model,
            profiles=profiles,
            operations=(revolve,),
            chord_tolerance=0.25,
            profile_samples=2049,
        )

    partial = create_revolve_operation(
        model,
        profiles[0],
        profile_feature_id=model.features[0].feature_id,
        axis_feature_id=model.features[1].feature_id,
        angle_degrees=180.0,
    )
    partial_preview = tessellate_design_preview(
        model,
        profiles=profiles,
        operations=(partial,),
        chord_tolerance=0.25,
        profile_samples=12,
        maximum_angular_segments=64,
    )[0]
    assert len(partial_preview.mesh.vertices) % 12 == 0
    assert len(partial_preview.mesh.vertices) // 12 >= 9


def test_invalid_or_stale_preview_operations_reject_without_authority_promotion() -> None:
    model, profiles, sections, operations = _document_parts()
    revised_model = revise_design_model_revision(
        model,
        parameters=model.parameters,
        features=model.features,
        actor_id="operator-2",
        reason="Changed revision for stale preview test.",
        created_at_utc="2026-10-03T13:00:00Z",
    )
    stale = operations[0]
    with pytest.raises(DesignPreviewError, match="operation_model_or_authority_stale"):
        tessellate_design_preview(
            revised_model,
            profiles=profiles,
            cross_sections=sections,
            operations=(stale,),
            chord_tolerance=0.25,
        )
    with pytest.raises(DesignPreviewError, match="revolve_preview_inputs_unsupported_or_stale"):
        tessellate_design_preview(
            model,
            profiles=(),
            operations=(stale,),
            chord_tolerance=0.25,
        )
