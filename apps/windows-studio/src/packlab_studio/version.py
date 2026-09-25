"""Local-only PackLab Studio version and update information."""

from __future__ import annotations

import json
import os
import platform
import sys
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from PySide6.QtWidgets import QFormLayout, QLabel, QWidget

from packlab_core.packscan.container import SCHEMA_VERSION

from . import __version__


class ManifestStatus(StrEnum):
    NO_MANIFEST = "no-manifest"
    CURRENT = "current"
    AVAILABLE = "available-local-manifest"
    MALFORMED = "malformed-manifest"
    UNSUPPORTED = "unsupported-manifest"


@dataclass(frozen=True, slots=True)
class BuildInfo:
    studio_version: str
    python_version: str
    qt_version: str
    packscan_schema: str
    build_revision: str


@dataclass(frozen=True, slots=True)
class VersionReport:
    current: BuildInfo
    status: ManifestStatus
    available_version: str | None = None
    manifest_revision: str | None = None


def current_build_info() -> BuildInfo:
    from PySide6 import __version__ as qt_version

    revision = os.environ.get("PACKLAB_BUILD_REVISION", "unknown")
    if not revision.isalnum() and revision != "unknown":
        revision = "unknown"
    return BuildInfo(__version__, platform.python_version() or sys.version.split()[0], qt_version, SCHEMA_VERSION, revision)


def read_local_manifest(path: str | Path | None) -> tuple[ManifestStatus, str | None, str | None]:
    if path is None or not Path(path).exists():
        return ManifestStatus.NO_MANIFEST, None, None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return ManifestStatus.MALFORMED, None, None
    if not isinstance(value, dict):
        return ManifestStatus.MALFORMED, None, None
    if value.get("schema_version") != 1:
        return ManifestStatus.UNSUPPORTED, None, None
    version = value.get("version")
    revision = value.get("revision")
    if not isinstance(version, str) or not version or (revision is not None and not isinstance(revision, str)):
        return ManifestStatus.MALFORMED, None, None
    return ManifestStatus.CURRENT if version == __version__ else ManifestStatus.AVAILABLE, version, revision


def version_report(manifest: str | Path | None = None) -> VersionReport:
    status, version, revision = read_local_manifest(manifest)
    return VersionReport(current_build_info(), status, version, revision)


class AboutView(QWidget):
    def __init__(self, report: VersionReport | None = None) -> None:
        super().__init__()
        self.setObjectName("packlab.view.about")
        report = report or version_report()
        layout = QFormLayout(self)
        values = {
            "PackLab Studio": report.current.studio_version,
            "Python": report.current.python_version,
            "Qt / PySide6": report.current.qt_version,
            "PackScan schema": report.current.packscan_schema,
            "Build revision": report.current.build_revision,
            "Local update manifest": report.status.value,
        }
        for label, value in values.items():
            layout.addRow(QLabel(label), QLabel(value))
