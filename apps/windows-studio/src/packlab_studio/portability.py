"""Read-only M06 project portability scanning and redacted reporting."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path, PureWindowsPath

from .project import ProjectMetadata
from .project_layout import ProjectLayout, ProjectLayoutError, safe_relative_path


class PortabilityClassification(StrEnum):
    REQUIRED_MISSING = "required-missing"
    EXTERNAL_PRESENT = "external-but-present"
    REGENERABLE_DERIVED = "regenerable-derived-cache"
    PORTABLE_PROJECT_OWNED = "portable-project-owned"
    UNSAFE_LINK = "unsafe-link"


@dataclass(frozen=True, slots=True)
class PortabilityFinding:
    classification: PortabilityClassification
    reference_id: str
    source_record: str
    required: bool
    exists: bool
    symlink: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification.value,
            "reference_id": self.reference_id,
            "source_record": self.source_record,
            "required": self.required,
            "exists": self.exists,
            "symlink": self.symlink,
        }


@dataclass(frozen=True, slots=True)
class PortabilityReport:
    schema_version: str
    project_id: str | None
    portable: bool
    integrity: dict[str, str]
    findings: tuple[PortabilityFinding, ...]
    raw_file_count: int
    raw_digest: str

    def to_dict(self) -> dict[str, object]:
        """Return a portable report with no absolute path or payload values."""

        return {
            "schema_version": self.schema_version,
            "project_id": self.project_id,
            "portable": self.portable,
            "integrity": dict(self.integrity),
            "findings": [finding.to_dict() for finding in self.findings],
            "raw_evidence": {
                "immutable": self.integrity.get("raw_evidence") == "pass",
                "file_count": self.raw_file_count,
                "aggregate_digest": self.raw_digest,
            },
        }

    def classifications(self, classification: PortabilityClassification) -> tuple[PortabilityFinding, ...]:
        return tuple(item for item in self.findings if item.classification is classification)


class PortabilityScanner:
    """Scan a project without copying assets or writing project state."""

    _REFERENCE_KEYS = frozenset(
        {
            "path",
            "asset",
            "asset_path",
            "source_path",
            "reference",
            "reference_path",
            "file",
            "uri",
        }
    )
    _PATH_SUFFIXES = (".obj", ".ply", ".xyz", ".pts", ".pcd", ".stl", ".step", ".stp")
    _SECRET_PATTERN = re.compile(r"(token|password|secret|api[_-]?key|private[_-]?key)", re.I)

    def scan(self, root: str | Path) -> PortabilityReport:
        project_root = Path(root)
        integrity: dict[str, str] = {}
        findings: list[PortabilityFinding] = []
        project_id: str | None = None
        try:
            layout = ProjectLayout.open(project_root)
            integrity["layout"] = "pass"
        except (OSError, ProjectLayoutError):
            return PortabilityReport("1.0", None, False, {"layout": "fail"}, (), 0, "")

        metadata_path = layout.path("working", "project.json")
        try:
            metadata = ProjectMetadata.from_dict(json.loads(metadata_path.read_text(encoding="utf-8")))
            project_id = metadata.project_id
            integrity["project_metadata"] = "pass"
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            integrity["project_metadata"] = "fail"

        self._check_json_integrity(layout, "history", "history", integrity)
        self._check_json_integrity(layout, "derived", "provenance", integrity)
        raw_count, raw_digest = self._raw_digest(layout)
        integrity["raw_evidence"] = "pass"

        for area in ("working", "history", "recovery", "derived", "cache"):
            area_root = layout.path(area)
            for path in sorted(area_root.rglob("*.json")):
                if path.is_symlink() and not self._is_within(path.resolve(), project_root.resolve()):
                    findings.append(
                        self._finding(
                            PortabilityClassification.UNSAFE_LINK,
                            str(path.relative_to(project_root)),
                            record=str(path.relative_to(project_root)),
                            required=True,
                            exists=True,
                            symlink=True,
                        )
                    )
                    continue
                try:
                    value = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    continue
                self._extract_references(
                    value,
                    layout=layout,
                    project_root=project_root,
                    record=str(path.relative_to(project_root)).replace("\\", "/"),
                    findings=findings,
                )

        for area in ("working", "history"):
            area_root = layout.path(area)
            for path in sorted(area_root.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    findings.append(
                        self._finding(
                            PortabilityClassification.PORTABLE_PROJECT_OWNED,
                            str(path.relative_to(project_root)),
                            record=str(path.relative_to(project_root)),
                            required=True,
                            exists=True,
                        )
                    )
        for area in ("derived", "cache"):
            area_root = layout.path(area)
            for path in sorted(area_root.rglob("*")):
                if path.is_file() and not path.is_symlink():
                    findings.append(
                        self._finding(
                            PortabilityClassification.REGENERABLE_DERIVED,
                            str(path.relative_to(project_root)),
                            record=str(path.relative_to(project_root)),
                            required=False,
                            exists=True,
                        )
                    )

        # The report is non-portable only for required missing or unsafe references.
        portable = not any(
            item.classification
            in {PortabilityClassification.REQUIRED_MISSING, PortabilityClassification.UNSAFE_LINK}
            for item in findings
        ) and all(value == "pass" for value in integrity.values())
        return PortabilityReport(
            "1.0", project_id, portable, integrity, tuple(findings), raw_count, raw_digest
        )

    def _extract_references(
        self,
        value: object,
        *,
        layout: ProjectLayout,
        project_root: Path,
        record: str,
        findings: list[PortabilityFinding],
        key: str = "",
        required: bool = True,
        regenerable: bool = False,
    ) -> None:
        if isinstance(value, dict):
            local_required = bool(value.get("required", required))
            local_regenerable = bool(value.get("regenerable", regenerable))
            for child_key, child in value.items():
                self._extract_references(
                    child,
                    layout=layout,
                    project_root=project_root,
                    record=record,
                    findings=findings,
                    key=str(child_key),
                    required=local_required,
                    regenerable=local_regenerable,
                )
            return
        if isinstance(value, list):
            for child in value:
                self._extract_references(
                    child,
                    layout=layout,
                    project_root=project_root,
                    record=record,
                    findings=findings,
                    key=key,
                    required=required,
                    regenerable=regenerable,
                )
            return
        if not isinstance(value, str) or not self._is_reference_value(value, key):
            return
        normalized = value.replace("\\", "/")
        is_absolute = Path(value).is_absolute() or PureWindowsPath(value).is_absolute()
        if is_absolute:
            candidate = Path(value)
            if not candidate.exists():
                classification = PortabilityClassification.REQUIRED_MISSING if required else PortabilityClassification.EXTERNAL_PRESENT
                findings.append(self._finding(classification, value, record=record, required=required, exists=False))
                return
            resolved = candidate.resolve(strict=False)
            if self._is_within(resolved, project_root.resolve()):
                self._record_project_path(
                    resolved, project_root, record, findings, required=required, regenerable=regenerable
                )
            else:
                findings.append(
                    self._finding(
                        PortabilityClassification.EXTERNAL_PRESENT,
                        value,
                        record=record,
                        required=required,
                        exists=True,
                        symlink=candidate.is_symlink(),
                    )
                )
            return
        try:
            safe = safe_relative_path(value)
            area = safe.parts[0]
            if area not in {"raw", "working", "derived", "cache", "temp", "export", "history", "recovery"}:
                return
            candidate = layout.path(area, Path(*safe.parts[1:])) if len(safe.parts) > 1 else layout.path(area)
        except ProjectLayoutError:
            findings.append(
                self._finding(
                    PortabilityClassification.UNSAFE_LINK,
                    normalized,
                    record=record,
                    required=required,
                    exists=False,
                )
            )
            return
        if candidate.is_symlink() and not self._is_within(candidate.resolve(strict=False), project_root.resolve()):
            findings.append(
                self._finding(
                    PortabilityClassification.UNSAFE_LINK,
                    normalized,
                    record=record,
                    required=required,
                    exists=candidate.exists(),
                    symlink=True,
                )
            )
        elif candidate.exists():
            self._record_project_path(
                candidate, project_root, record, findings, required=required, regenerable=regenerable
            )
        elif required:
            findings.append(
                self._finding(
                    PortabilityClassification.REQUIRED_MISSING,
                    normalized,
                    record=record,
                    required=True,
                    exists=False,
                )
            )

    def _record_project_path(
        self,
        candidate: Path,
        project_root: Path,
        record: str,
        findings: list[PortabilityFinding],
        *,
        required: bool,
        regenerable: bool,
    ) -> None:
        try:
            relative = candidate.resolve(strict=False).relative_to(project_root.resolve())
        except ValueError:
            findings.append(self._finding(PortabilityClassification.EXTERNAL_PRESENT, str(candidate), record=record, required=required, exists=True))
            return
        area = relative.parts[0] if relative.parts else ""
        classification = (
            PortabilityClassification.REGENERABLE_DERIVED
            if regenerable or area in {"derived", "cache", "temp"}
            else PortabilityClassification.PORTABLE_PROJECT_OWNED
        )
        findings.append(
            self._finding(classification, str(relative), record=record, required=required, exists=candidate.exists(), symlink=candidate.is_symlink())
        )

    def _check_json_integrity(self, layout: ProjectLayout, area: str, name: str, integrity: dict[str, str]) -> None:
        target = layout.path(area, f"{name}.json")
        if not target.exists():
            integrity[name] = "pass"
            return
        try:
            json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            integrity[name] = "fail"
        else:
            integrity[name] = "pass"

    @staticmethod
    def _is_reference_value(value: str, key: str) -> bool:
        if PortabilityScanner._SECRET_PATTERN.search(key):
            return False
        normalized = value.replace("\\", "/")
        return key.lower() in PortabilityScanner._REFERENCE_KEYS or normalized.startswith(tuple(f"{area}/" for area in ("raw", "working", "derived", "cache", "temp", "export", "history", "recovery"))) or normalized.lower().endswith(PortabilityScanner._PATH_SUFFIXES)

    @staticmethod
    def _finding(
        classification: PortabilityClassification,
        reference: str,
        *,
        record: str,
        required: bool,
        exists: bool,
        symlink: bool = False,
    ) -> PortabilityFinding:
        digest = hashlib.sha256(reference.encode("utf-8", errors="replace")).hexdigest()[:16]
        return PortabilityFinding(classification, f"ref-{digest}", record, required, exists, symlink)

    @staticmethod
    def _is_within(candidate: Path, root: Path) -> bool:
        try:
            os.path.commonpath((str(candidate), str(root))) == str(root)
        except ValueError:
            return False
        return os.path.commonpath((str(candidate), str(root))) == str(root)

    @staticmethod
    def _raw_digest(layout: ProjectLayout) -> tuple[int, str]:
        digest = hashlib.sha256()
        files = sorted(path for path in layout.path("raw").rglob("*") if path.is_file())
        for path in files:
            digest.update(str(path.relative_to(layout.root)).replace("\\", "/").encode())
            digest.update(path.read_bytes())
        return len(files), digest.hexdigest()


def scan_project_portability(root: str | Path) -> PortabilityReport:
    """Production entry point for the M06 project portability report/plan."""

    return PortabilityScanner().scan(root)
