from __future__ import annotations

import platform
import sys
from types import ModuleType, SimpleNamespace

import pytest

from packlab_core.geometry_adapter import (
    OPEN3D_VERSION,
    CapabilityStatus,
    GeometryCapabilityUnavailable,
    InvalidGeometry,
    Open3DGeometryAdapter,
    PointCloudData,
    TriangleMeshData,
    probe_open3d,
)


def test_open3d_exact_version_build_and_geometry_capabilities_are_reported():
    capability = probe_open3d()

    assert capability.status is CapabilityStatus.AVAILABLE
    assert capability.expected_version == "0.20.0"
    assert capability.observed_version == OPEN3D_VERSION
    assert capability.python_version == platform.python_version()
    assert capability.machine == platform.machine()
    assert "point_cloud_conversion" in capability.operations
    assert "triangle_mesh_conversion" in capability.operations
    config = dict(capability.build_config)
    assert isinstance(config["BUILD_CUDA_MODULE"], bool)
    assert isinstance(config["BUILD_SYCL_MODULE"], bool)
    assert config["CMAKE_BUILD_TYPE"] == "Release"


@pytest.mark.skipif(
    sys.platform != "win32" or sys.version_info[:2] != (3, 12),
    reason="proves the supported native Windows CPython 3.12 PackLab environment",
)
def test_selected_artifact_runs_on_windows_cpython_312():
    capability = probe_open3d()

    assert capability.status is CapabilityStatus.AVAILABLE
    assert capability.observed_version == "0.20.0"
    assert capability.machine == "AMD64"
    config = dict(capability.build_config)
    assert config["BUILD_CUDA_MODULE"] is False
    assert config["BUILD_SYCL_MODULE"] is False
    assert config["BUILD_PYTORCH_OPS"] is True
    assert config["Pytorch_VERSION"] == "2.13.0+cpu"


def test_packlab_point_cloud_round_trip_preserves_values_and_attributes():
    cloud = PointCloudData(
        points=((1.0, 2.0, 3.0), (-4.5, 0.0, 8.25)),
        colors=((0.1, 0.2, 0.3), (1.0, 0.0, 0.5)),
        normals=((0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    )

    assert Open3DGeometryAdapter().round_trip_point_cloud(cloud) == cloud


def test_packlab_triangle_mesh_round_trip_preserves_topology_and_attributes():
    mesh = TriangleMeshData(
        vertices=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
        triangles=((0, 1, 2),),
        vertex_colors=((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        vertex_normals=((0.0, 0.0, 1.0),) * 3,
    )

    assert Open3DGeometryAdapter().round_trip_triangle_mesh(mesh) == mesh


def test_unavailable_package_is_reported_without_install_or_download_fallback():
    calls: list[str] = []

    def missing_package() -> ModuleType:
        calls.append("import")
        raise ModuleNotFoundError("open3d is absent", name="open3d")

    adapter = Open3DGeometryAdapter(missing_package)
    capability = adapter.probe()

    assert capability.status is CapabilityStatus.UNAVAILABLE
    # Distribution metadata can remain present even if the importable module is not.
    assert capability.observed_version == OPEN3D_VERSION
    assert calls == ["import"]
    with pytest.raises(GeometryCapabilityUnavailable, match="import unavailable"):
        adapter.round_trip_point_cloud(PointCloudData(points=((0.0, 0.0, 0.0),)))
    assert calls == ["import", "import"]


def test_wrong_version_or_missing_build_facts_stays_unknown():
    module = ModuleType("open3d")
    module.__version__ = "0.21.0"
    module._build_config = {"BUILD_CUDA_MODULE": False}
    module.geometry = SimpleNamespace(PointCloud=object, TriangleMesh=object)
    module.utility = SimpleNamespace(Vector3dVector=object, Vector3iVector=object)

    capability = probe_open3d(lambda: module)

    assert capability.status is CapabilityStatus.UNKNOWN
    assert "expected exact pin" in capability.detail


def test_public_geometry_contract_rejects_invalid_values_before_backend_conversion():
    with pytest.raises(InvalidGeometry, match="finite numbers"):
        PointCloudData(points=((float("nan"), 0.0, 0.0),))
    with pytest.raises(InvalidGeometry, match="match the point count"):
        PointCloudData(points=((0.0, 0.0, 0.0),), colors=())
    with pytest.raises(InvalidGeometry, match="in range"):
        TriangleMeshData(vertices=((0.0, 0.0, 0.0),), triangles=((0, 1, 0),))


def test_domain_contract_annotations_do_not_expose_open3d_classes():
    exposed = repr(
        (
            PointCloudData.__annotations__,
            TriangleMeshData.__annotations__,
            Open3DGeometryAdapter.__annotations__,
        )
    ).lower()

    assert "open3d.geometry" not in exposed
    assert "moduletype" not in exposed
