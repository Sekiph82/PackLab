from __future__ import annotations

from tools.viewport_benchmark import run_benchmark

from packlab_studio.viewport import MeshGeometry, PointCloudGeometry
from packlab_studio.viewport_lod import LODPolicy, display_geometry


def test_lod_thresholds_and_stable_display_counts() -> None:
    policy = LODPolicy(display_budget=4)
    assert policy.plan(4).to_dict()["level"] == "full"
    first = policy.plan(17)
    second = policy.plan(17)
    assert first == second
    assert first.display_count <= 4
    assert first.stride == 5


def test_lod_point_cloud_does_not_mutate_source_and_falls_back_without_decimator() -> None:
    source = PointCloudGeometry(tuple((float(index), 0.0, 0.0) for index in range(10)))
    display, plan = display_geometry(source, LODPolicy(display_budget=3))
    assert isinstance(display, PointCloudGeometry)
    assert len(source.points) == 10
    assert len(display.points) == plan.display_count == 3
    fallback, fallback_plan = display_geometry(source, LODPolicy(display_budget=3, decimation_available=False))
    assert fallback == source
    assert fallback_plan.decimation == "fallback-no-decimator"


def test_lod_mesh_remaps_only_display_representation() -> None:
    source = MeshGeometry(
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 1.0, 0.0)),
        ((0, 1, 2), (1, 3, 2)),
    )
    display, plan = display_geometry(source, LODPolicy(display_budget=1))
    assert isinstance(display, MeshGeometry)
    assert plan.display_count == len(display.triangles) == 1
    assert source.triangles == ((0, 1, 2), (1, 3, 2))


def test_benchmark_result_schema_records_lod_and_truthful_gpu_limit() -> None:
    result = run_benchmark((8, 20))
    assert result["runtime"]["native_gpu_claim"] is False
    assert result["policy"]["display_budget"] == 10_000
    assert [item["source_count"] for item in result["results"]] == [8, 20]
    assert all("render_seconds" in item and "lod" in item for item in result["results"])
