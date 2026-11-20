from __future__ import annotations

from pathlib import Path

from packlab_studio import engine_config
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
    assert (
        report.for_engine("openmvs.densify_point_cloud").executable
        == root / "DensifyPointCloud.exe"
    )
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


_OPENMVS = ("InterfaceCOLMAP", "DensifyPointCloud", "ReconstructMesh", "RefineMesh", "TextureMesh")


def _exe(name: str) -> str:
    return engine_config._windows_executable(name)


def _bundled_layout(root: Path) -> None:
    (root / "colmap" / "bin").mkdir(parents=True)
    (root / "openmvs").mkdir()
    for path in [root / "colmap" / "bin" / _exe("colmap")] + [
        root / "openmvs" / _exe(name) for name in _OPENMVS
    ]:
        path.write_bytes(b"bundled")
        path.chmod(0o755)


def test_bundled_engines_resolve_before_path(tmp_path) -> None:
    engines = tmp_path / "engines"
    _bundled_layout(engines)
    report = discover_engines(
        environment={},
        which=lambda _command: str(tmp_path / "path.exe"),
        bundled_roots=(tmp_path / "absent", engines),
    )
    for record in report.records:
        assert record.source == "bundled", record
        assert record.status is DiscoveryStatus.CONFIGURED
    assert report.for_engine("colmap").executable == engines / "colmap" / "bin" / _exe("colmap")
    texture = report.for_engine("openmvs.texture_mesh")
    assert texture.executable == engines / "openmvs" / _exe("TextureMesh")
    assert report.as_dict()["engines"][0]["source"] == "bundled"


def test_explicit_and_environment_override_bundled(tmp_path) -> None:
    engines = tmp_path / "engines"
    _bundled_layout(engines)
    env_colmap = tmp_path / "env-colmap.exe"
    env_colmap.write_bytes(b"env")
    explicit_root = tmp_path / "explicit-openmvs"
    explicit_root.mkdir()
    report = discover_engines(
        EngineConfiguration(openmvs_root=explicit_root),
        environment={"PACKLAB_COLMAP_PATH": str(env_colmap)},
        bundled_roots=(engines,),
    )
    assert report.for_engine("colmap").source == "environment"
    assert report.for_engine("colmap").executable == env_colmap
    assert report.for_engine("openmvs.densify_point_cloud").source == "explicit"


def test_frozen_executable_uses_engines_beside_exe(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(engine_config.sys, "frozen", True, raising=False)
    monkeypatch.setattr(engine_config.sys, "executable", str(tmp_path / "PackLabStudio.exe"))
    assert engine_config.default_bundled_engine_roots() == (tmp_path.resolve() / "engines",)


def test_ownerdev_runtime_also_uses_shared_owner_engines(tmp_path, monkeypatch) -> None:
    runtime = tmp_path / "OwnerDev" / "current"
    module = runtime / "apps" / "windows-studio" / "src" / "packlab_studio" / "engine_config.py"
    module.parent.mkdir(parents=True)
    (runtime / "owner-dev-runtime.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(engine_config, "__file__", str(module))
    roots = engine_config.default_bundled_engine_roots()
    assert roots == (runtime.resolve() / "engines", (tmp_path / "OwnerDev").resolve() / "engines")
