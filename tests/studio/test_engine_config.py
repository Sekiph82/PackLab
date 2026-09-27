from __future__ import annotations

from packlab_studio.engine_config import (
    DiscoveryStatus,
    EngineConfiguration,
    discover_engines,
)


def test_explicit_paths_take_precedence_over_path_lookup(tmp_path) -> None:
    colmap = tmp_path / "colmap.exe"
    colmap.write_bytes(b"fixture")
    path_candidate = tmp_path / "path-colmap.exe"
    path_candidate.write_bytes(b"path")
    report = discover_engines(
        EngineConfiguration(colmap_path=colmap),
        which=lambda command: str(path_candidate) if command == "colmap.exe" else None,
    )
    record = report.for_engine("colmap")
    assert record.status is DiscoveryStatus.CONFIGURED
    assert record.source == "explicit"
    assert record.executable == colmap


def test_openmvs_root_resolves_only_known_stage_executables(tmp_path) -> None:
    root = tmp_path / "openmvs"
    root.mkdir()
    (root / "DensifyPointCloud.exe").write_bytes(b"fixture")
    report = discover_engines(
        EngineConfiguration(openmvs_root=root, allow_path_lookup=False),
    )
    assert report.for_engine("openmvs.densify_point_cloud").status is DiscoveryStatus.CONFIGURED
    assert report.for_engine("openmvs.densify_point_cloud").executable == root / "DensifyPointCloud.exe"
    assert report.for_engine("openmvs.reconstruct_mesh").status is DiscoveryStatus.MISSING


def test_missing_and_invalid_configuration_are_diagnostic_only(tmp_path) -> None:
    report = discover_engines(
        EngineConfiguration(colmap_path=tmp_path / "missing.exe", allow_path_lookup=False),
    )
    assert report.for_engine("colmap").status is DiscoveryStatus.MISSING
    directory = tmp_path / "directory"
    directory.mkdir()
    report = discover_engines(
        EngineConfiguration(colmap_path=directory, allow_path_lookup=False),
    )
    assert report.for_engine("colmap").status is DiscoveryStatus.INVALID
    assert not (tmp_path / "download").exists()


def test_environment_path_is_explicit_and_no_path_scan_when_disabled(tmp_path) -> None:
    colmap = tmp_path / "env-colmap.exe"
    colmap.write_bytes(b"fixture")
    report = discover_engines(
        EngineConfiguration(allow_path_lookup=False),
        environment={"PACKLAB_COLMAP_PATH": str(colmap)},
        which=lambda _command: (_ for _ in ()).throw(AssertionError("PATH lookup was not allowed")),
    )
    assert report.for_engine("colmap").source == "environment"
    assert report.for_engine("colmap").status is DiscoveryStatus.CONFIGURED
