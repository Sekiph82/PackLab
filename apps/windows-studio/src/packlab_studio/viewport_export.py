"""Atomic, redacted viewport preview export."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize

from .viewport import ViewportService


class ViewportExportError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ViewportExportResult:
    image_path: Path
    metadata_path: Path
    width: int
    height: int


class ViewportPreviewExporter:
    """Publish only explicit preview outputs, never raw source evidence."""

    def export(
        self,
        service: ViewportService,
        destination: str | Path,
        *,
        project_id: str | None = None,
        revision: int | None = None,
        project_root: str | Path | None = None,
        image_format: str | None = None,
        overwrite: bool = False,
        size: QSize = QSize(960, 640),
    ) -> ViewportExportResult:
        target = Path(destination)
        fmt = (image_format or target.suffix.lstrip(".") or "png").lower()
        if fmt != "png":
            raise ViewportExportError("only deterministic PNG preview export is supported")
        root = Path(project_root).resolve() if project_root is not None else None
        resolved_target = target.resolve(strict=False)
        if root is not None and self._is_within(resolved_target, root / "raw"):
            raise ViewportExportError("raw evidence cannot be overwritten by a preview")
        if target.exists() and not overwrite:
            raise ViewportExportError("preview destination exists; explicit overwrite is required")
        target.parent.mkdir(parents=True, exist_ok=True)
        metadata_path = target.with_suffix(".json")
        if metadata_path.exists() and not overwrite:
            raise ViewportExportError("preview metadata destination exists; explicit overwrite is required")
        try:
            image = service.render(size)
        except Exception as error:
            raise ViewportExportError("selected viewport backend is unavailable") from error
        if image.isNull():
            raise ViewportExportError("viewport backend returned an empty image")
        metadata = {
            "schema_version": "1.0",
            "project_id": project_id,
            "revision": revision,
            "format": "png",
            "width": image.width(),
            "height": image.height(),
            "viewport_backend": service.adapter.backend_name,
            "viewport_backend_version": service.adapter.backend_version,
            "camera": service.state.camera.to_dict(),
            "visible_object_ids": [item.object_id for item in service.scene.visible_objects()],
            "capabilities": service.adapter.capabilities(),
            "paths_redacted": True,
        }
        self._atomic_image(target, image)
        self._atomic_json(metadata_path, metadata)
        return ViewportExportResult(target, metadata_path, image.width(), image.height())

    @staticmethod
    def _atomic_image(target: Path, image) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
        os.close(fd)
        temporary = Path(temporary_name)
        try:
            if not image.save(str(temporary), "PNG"):
                raise ViewportExportError("viewport image encoding failed")
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _atomic_json(target: Path, value: object) -> None:
        fd, temporary_name = tempfile.mkstemp(prefix=f".{target.name}-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                json.dump(value, handle, sort_keys=True, separators=(",", ":"))
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary_name, target)
        finally:
            Path(temporary_name).unlink(missing_ok=True)

    @staticmethod
    def _is_within(candidate: Path, root: Path) -> bool:
        try:
            return os.path.commonpath((str(candidate), str(root))) == str(root)
        except ValueError:
            return False


def export_viewport_preview(
    service: ViewportService, destination: str | Path, **kwargs: Any
) -> ViewportExportResult:
    return ViewportPreviewExporter().export(service, destination, **kwargs)
