from __future__ import annotations

from pathlib import Path

import pytest

from packlab_core.engine_probe import (
    OPENMVS_COMPONENTS,
    EngineProbeStatus,
    EngineVersion,
    parse_colmap_version,
    probe_colmap,
    probe_openmvs,
    probe_openmvs_components,
)


def _runner(output: str, returncode: int = 0, expected_args: tuple[str, ...] | None = None):
    def run(_path: Path, args: tuple[str, ...]) -> tuple[int, str, str]:
        if expected_args is not None:
            assert args == expected_args
        return returncode, output, ""

    return run


def test_colmap_parser_accepts_the_selected_banner() -> None:
    assert parse_colmap_version(
        "COLMAP 3.12.6 -- Structure-from-Motion and Multi-View Stereo"
    ) == EngineVersion(3, 12, 6)


def test_colmap_help_fixture_is_command_sensitive(tmp_path) -> None:
    executable = tmp_path / "colmap.exe"
    executable.write_bytes(b"fixture")
    output = "COLMAP 3.12.6 -- Structure-from-Motion and Multi-View Stereo\nUsage: colmap help"
    result = probe_colmap(executable, runner=_runner(output, expected_args=("help",)))
    assert result.status is EngineProbeStatus.VALID


def test_wrong_colmap_argv_fails_the_fixture(tmp_path) -> None:
    executable = tmp_path / "colmap.exe"
    executable.write_bytes(b"fixture")

    def run(_path: Path, args: tuple[str, ...]) -> tuple[int, str, str]:
        assert args == ("help",)
        return 0, "COLMAP 3.12.6", ""

    with pytest.raises(AssertionError):
        probe_colmap(executable, runner=lambda path, args: run(path, ("--version",)))


def test_probe_distinguishes_missing_invalid_unsupported_and_valid(tmp_path) -> None:
    missing = probe_colmap(tmp_path / "missing.exe", runner=_runner(""))
    assert missing.status is EngineProbeStatus.MISSING
    assert missing.configured is True

    executable = tmp_path / "colmap.exe"
    executable.write_bytes(b"fixture")
    invalid = probe_colmap(executable, runner=_runner("COLMAP unavailable"))
    assert invalid.status is EngineProbeStatus.INVALID

    unsupported = probe_colmap(executable, runner=_runner("COLMAP 4.0.0"))
    assert unsupported.status is EngineProbeStatus.UNSUPPORTED
    assert unsupported.version == EngineVersion(4, 0, 0)

    valid = probe_colmap(executable, runner=_runner("COLMAP 3.12.6"))
    assert valid.status is EngineProbeStatus.VALID
    assert valid.version == EngineVersion(3, 12, 6)


def test_probe_reports_unexecutable_runner_failure_without_writing(tmp_path) -> None:
    executable = tmp_path / "colmap.exe"
    executable.write_bytes(b"fixture")
    before = executable.read_bytes()
    result = probe_colmap(executable, runner=_runner("", returncode=17))
    assert result.status is EngineProbeStatus.UNEXECUTABLE
    assert executable.read_bytes() == before


def test_openmvs_help_fixture_accepts_expected_no_input_exit(tmp_path) -> None:
    executable = tmp_path / "DensifyPointCloud.exe"
    executable.write_bytes(b"fixture")
    result = probe_openmvs(
        executable,
        runner=_runner(
            "OpenMVS x64 v2.4.0\nNo input scene supplied", returncode=1, expected_args=("-h",)
        ),
    )
    assert result.status is EngineProbeStatus.VALID
    assert result.version == EngineVersion(2, 4, 0)


def test_openmvs_nonzero_without_banner_is_not_valid(tmp_path) -> None:
    executable = tmp_path / "DensifyPointCloud.exe"
    executable.write_bytes(b"fixture")
    result = probe_openmvs(
        executable, runner=_runner("unknown option", returncode=1, expected_args=("-h",))
    )
    assert result.status is EngineProbeStatus.INVALID


def test_openmvs_unexpected_exit_is_unexecutable_even_with_banner(tmp_path) -> None:
    executable = tmp_path / "DensifyPointCloud.exe"
    executable.write_bytes(b"fixture")
    result = probe_openmvs(executable, runner=_runner("OpenMVS x64 v2.4.0", returncode=2))
    assert result.status is EngineProbeStatus.UNEXECUTABLE


def test_openmvs_missing_is_explicit() -> None:
    result = probe_openmvs(None)
    assert result.status is EngineProbeStatus.MISSING
    assert result.detail == "no executable configured"


def test_openmvs_component_suite_reports_each_component_and_readiness(tmp_path) -> None:
    paths = {}
    for component in OPENMVS_COMPONENTS:
        path = tmp_path / f"{component}.exe"
        path.write_bytes(b"fixture")
        paths[component] = path

    calls: dict[str, tuple[str, ...]] = {}

    def runner(path: Path, args: tuple[str, ...]) -> tuple[int, str, str]:
        calls[path.stem] = args
        return 1, "OpenMVS x64 v2.4.0", ""

    suite = probe_openmvs_components(paths, runner=runner)
    assert suite.ready
    assert [result.executable for result in suite.components] == [
        str(paths[name]) for name in OPENMVS_COMPONENTS
    ]
    assert set(calls.values()) == {("-h",)}

    missing = dict(paths)
    missing.pop("InterfaceCOLMAP")
    assert not probe_openmvs_components(missing, runner=runner).ready

    def unsupported_runner(path: Path, args: tuple[str, ...]) -> tuple[int, str, str]:
        if path.stem == "ReconstructMesh":
            return 1, "OpenMVS x64 v3.0.0", ""
        return runner(path, args)

    unsupported_suite = probe_openmvs_components(paths, runner=unsupported_runner)
    assert not unsupported_suite.ready
    assert unsupported_suite.components[2].status is EngineProbeStatus.UNSUPPORTED

    def invalid_runner(path: Path, args: tuple[str, ...]) -> tuple[int, str, str]:
        if path.stem == "TextureMesh":
            return 17, "", "crash"
        return runner(path, args)

    invalid_suite = probe_openmvs_components(paths, runner=invalid_runner)
    assert not invalid_suite.ready
    assert invalid_suite.components[4].status is EngineProbeStatus.UNEXECUTABLE
