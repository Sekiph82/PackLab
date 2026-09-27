"""Pinned external-engine evidence used by the PackLab reconstruction boundary."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class EngineBaseline:
    engine_id: str
    version: str
    source_url: str
    source_ref: str
    source_revision: str
    license_name: str
    license_url: str
    build_source: str
    integration_mode: str
    binary_sha256: str | None
    host_validation: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


COLMAP_BASELINE = EngineBaseline(
    engine_id="colmap",
    version="3.12.6",
    source_url="https://github.com/colmap/colmap",
    source_ref="3.12.6",
    source_revision="4d5b60e19ad268072adaf1267d21fa38a9a828ca",
    license_name="New BSD / 3-clause BSD for COLMAP itself; third-party dependencies require separate review",
    license_url="https://colmap.github.io/license.html",
    build_source="Official GitHub release tag with Windows pre-built binaries or reproducible source build through vcpkg",
    integration_mode="external executable discovered by explicit path or safe PATH lookup; not bundled by PackLab",
    binary_sha256=None,
    host_validation="source identity recorded and parser fixtures tested; no COLMAP executable installed on the builder host",
)


OPENMVS_BASELINE = EngineBaseline(
    engine_id="openmvs",
    version="2.4.0",
    source_url="https://github.com/cdcseacave/openMVS",
    source_ref="v2.4.0",
    source_revision="58117204c86bbb11a0b25b26a8987676cf11274d",
    license_name="GNU AGPL-3.0; HIGH LICENSE ATTENTION; no distribution-clearance conclusion",
    license_url="https://github.com/cdcseacave/openMVS/blob/v2.4.0/LICENSE",
    build_source="Official GitHub release with Windows x64 assets or reproducible source build; PackLab does not bundle or auto-download it",
    integration_mode="external executable discovered by explicit configuration or safe PATH lookup; not bundled by PackLab",
    binary_sha256=None,
    host_validation="source identity recorded and parser fixtures tested; no OpenMVS executable installed on the builder host",
)


def baseline_records() -> tuple[EngineBaseline, ...]:
    return (COLMAP_BASELINE, OPENMVS_BASELINE)
