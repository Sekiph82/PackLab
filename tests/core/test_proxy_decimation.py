from __future__ import annotations

import hashlib
import json

import pytest

from packlab_core.geometry_adapter import TriangleMeshData, probe_open3d
from packlab_core.proxy_decimation import (
    PREVIEW_PROXY_AUTHORITY,
    ProxyDecimationError,
    ProxyDecimationPolicy,
    decimate_preview_proxy,
    reject_proxy_scan_master_promotion,
)
from packlab_core.reconstruction import ScaleState


def _grid_mesh(side: int = 12) -> TriangleMeshData:
    vertices = tuple(
        (float(column), float(row), 0.01 * ((row + column) % 2))
        for row in range(side)
        for column in range(side)
    )
    triangles = []
    for row in range(side - 1):
        for column in range(side - 1):
            top_left = row * side + column
            top_right = top_left + 1
            bottom_left = top_left + side
            bottom_right = bottom_left + 1
            triangles.extend(
                ((top_left, top_right, bottom_right), (top_left, bottom_right, bottom_left))
            )
    return TriangleMeshData(vertices, tuple(triangles))


def _digest(mesh: TriangleMeshData) -> str:
    payload = {
        "vertices": mesh.vertices,
        "triangles": mesh.triangles,
        "vertex_colors": mesh.vertex_colors,
        "vertex_normals": mesh.vertex_normals,
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
            "ascii"
        )
    ).hexdigest()


def _proxy(mesh: TriangleMeshData, target: int):
    return decimate_preview_proxy(
        mesh,
        full_parent_revision_id="full-cleaned-mesh-r1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
        scale_provenance_id="scale-provenance-r1",
        policy=ProxyDecimationPolicy(
            target_triangle_count=target,
            maximum_error_ratio=0.01,
            boundary_weight=10.0,
        ),
    )


def test_locked_open3d_build_exposes_the_selected_quadric_decimator() -> None:
    capability = probe_open3d()
    assert "triangle_mesh_quadric_decimation" in capability.operations


def test_decimation_reduces_triangle_and_vertex_counts_without_changing_full_parent() -> None:
    mesh = _grid_mesh()
    original = (mesh.vertices, mesh.triangles, mesh.vertex_colors, mesh.vertex_normals)
    parent_digest = _digest(mesh)

    result = _proxy(mesh, 32)

    assert result.proxy_mesh is not mesh
    assert result.quality.output_triangle_count < result.quality.input_triangle_count
    assert result.quality.output_vertex_count < result.quality.input_vertex_count
    assert result.quality.target_triangle_count == 32
    assert result.quality.triangle_reduction_fraction > 0
    assert result.quality.vertex_reduction_fraction > 0
    assert result.full_parent_mesh is mesh
    assert result.full_parent_geometry_sha256 == parent_digest == _digest(mesh)
    assert (mesh.vertices, mesh.triangles, mesh.vertex_colors, mesh.vertex_normals) == original
    assert result.quality.sampled_parent_to_proxy_max_distance >= 0
    assert result.quality.sampled_proxy_to_parent_max_distance >= 0


def test_noop_target_preserves_geometry_but_still_marks_proxy_authority() -> None:
    mesh = _grid_mesh(3)

    class NoProbeAdapter:
        def probe(self):
            raise AssertionError("no-op threshold must not invoke Open3D")

    result = decimate_preview_proxy(
        mesh,
        full_parent_revision_id="full-mesh-r1",
        scale_state=ScaleState.RELATIVE,
        policy=ProxyDecimationPolicy(target_triangle_count=len(mesh.triangles)),
        adapter=NoProbeAdapter(),  # type: ignore[arg-type]
    )

    assert result.proxy_mesh == mesh
    assert result.quality.triangle_reduction_fraction == 0
    assert result.operation_status == "NO_OP_TARGET_NOT_BELOW_PARENT_TRIANGLE_COUNT"
    assert result.authority_class == PREVIEW_PROXY_AUTHORITY
    assert result.scan_master_eligible is False


def test_identity_is_deterministic_parent_bound_and_carries_deferred_scale() -> None:
    mesh = _grid_mesh()
    first = _proxy(mesh, 32)
    second = _proxy(mesh, 32)

    assert first.as_dict() == second.as_dict()
    assert first.proxy_revision_id == second.proxy_revision_id
    assert first.full_parent_revision_id == "full-cleaned-mesh-r1"
    assert first.scale_state is ScaleState.METRIC_UNVERIFIED
    assert first.scale_provenance_id == "scale-provenance-r1"
    assert first.physical_accuracy_validation_status == "DEFERRED_OWNER_VALIDATION"
    assert first.mold_use_authorized is False


def test_texture_uv_limit_and_proxy_scan_master_rejection_are_explicit() -> None:
    result = _proxy(_grid_mesh(), 32)

    assert result.texture_uv_status == "UNAVAILABLE_IN_PACKLAB_GEOMETRY_CONTRACT"
    assert "textures" not in result.proxy_mesh.__dataclass_fields__
    assert "uv" not in result.proxy_mesh.__dataclass_fields__
    with pytest.raises(ProxyDecimationError, match="PREVIEW_PROXY"):
        reject_proxy_scan_master_promotion(result)


def test_invalid_targets_and_escalated_scale_state_fail_closed() -> None:
    with pytest.raises(ProxyDecimationError, match="positive integer"):
        ProxyDecimationPolicy(target_triangle_count=0)
    with pytest.raises(ProxyDecimationError, match="proxy bound"):
        ProxyDecimationPolicy(target_triangle_count=20_001)
    with pytest.raises(ProxyDecimationError, match="scale_state"):
        decimate_preview_proxy(
            _grid_mesh(),
            full_parent_revision_id="full-mesh-r1",
            scale_state=ScaleState.METRIC_VERIFIED,
            policy=ProxyDecimationPolicy(target_triangle_count=32),
        )
