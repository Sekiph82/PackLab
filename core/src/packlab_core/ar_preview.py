"""PL-0430 prototype: bounded AR preview package of an edited Design Model for iPhone.

Turns an existing ``CadPreviewMeshRevision`` (tessellated Design Model BREP) into a small,
digest-bound JSON document that the PackLab Capture app can render with RealityKit
(``packlab.ar-preview-mesh.v1``). Coordinates are converted from the model's
``mm_unverified`` (or relative) units to metres for display only; the document repeats
the source authority so the phone can show it, and it never carries Scan Master,
measurement or manufacturing authority. AR placement on a real surface is a visual
reference: on-device scale, tracking accuracy and physical fit are not validated
(pending physical iPhone 16 evidence). Traceability follows the PL-0233 authority model:
the package names the exact Design Model, BREP, preview and parent-authority revisions.
"""

from __future__ import annotations

import hashlib
import json
import math
from typing import Final

from .cad_preview import CadPreviewMeshRevision

AR_PREVIEW_CONTRACT: Final = "packlab.ar-preview-mesh.v1"
MAX_AR_VERTICES: Final = 65_535
MAX_AR_TRIANGLES: Final = 131_072
_UNIT_TO_METRES: Final = {"mm_unverified": 0.001}
_RELATIVE_UNITS: Final = frozenset({"reconstruction_units"})
MAX_AR_EXTENT_M: Final = 10.0  # matches the phone-side coordinate bound


class ArPreviewError(ValueError):
    """Raised when a preview mesh cannot be packaged safely for AR display."""


def _canonical(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode("ascii")


def build_ar_preview_package(preview: CadPreviewMeshRevision) -> bytes:
    """Return canonical JSON bytes for the phone; raises if bounds or authority are unsafe."""
    if not isinstance(preview, CadPreviewMeshRevision):
        raise ArPreviewError("cad_preview_required")
    if (
        preview.contract != "packlab.cad-brep-preview.v1"
        or preview.authority_class != "PREVIEW_PROXY"
        or preview.mold_use_authorized is not False
        or preview.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
    ):
        raise ArPreviewError("preview_authority_invalid")
    if (
        preview.coordinate_unit not in _UNIT_TO_METRES
        and preview.coordinate_unit not in _RELATIVE_UNITS
    ):
        raise ArPreviewError("preview_coordinate_unit_unsupported")
    mesh = preview.mesh
    if (
        not 3 <= len(mesh.vertices) <= MAX_AR_VERTICES
        or not 1 <= len(mesh.triangles) <= MAX_AR_TRIANGLES
    ):
        raise ArPreviewError("preview_mesh_size_out_of_bounds")
    low = [min(vertex[axis] for vertex in mesh.vertices) for axis in range(3)]
    high = [max(vertex[axis] for vertex in mesh.vertices) for axis in range(3)]
    scale = _UNIT_TO_METRES.get(preview.coordinate_unit)
    if scale is None:
        # Relative geometry has no metric meaning; show it at a nominal 0.1 m size instead.
        extent = max(high[axis] - low[axis] for axis in range(3))
        if not math.isfinite(extent) or extent <= 0.0:
            raise ArPreviewError("preview_bounds_invalid")
        scale = 0.1 / extent
        display_scale_basis = "RELATIVE_NORMALIZED_TO_0_1_M_DISPLAY_ONLY"
    else:
        display_scale_basis = "MM_UNVERIFIED_TO_METRES_DISPLAY_ONLY"
    # Centre on the footprint and rest on the base (z = 0), then convert source z-up to the
    # RealityKit y-up frame: (x, y, z) -> (x, z, -y).
    centre = ((low[0] + high[0]) / 2.0, (low[1] + high[1]) / 2.0, low[2])
    if max(high[axis] - low[axis] for axis in range(3)) * scale > MAX_AR_EXTENT_M:
        raise ArPreviewError("preview_extent_exceeds_display_bound")
    positions: list[float] = []
    for x, y, z in mesh.vertices:
        local = ((x - centre[0]) * scale, (y - centre[1]) * scale, (z - centre[2]) * scale)
        if not all(math.isfinite(value) for value in local):
            raise ArPreviewError("preview_vertex_invalid")
        positions.extend((round(local[0], 7), round(local[2], 7), round(-local[1], 7)))
    indices: list[int] = []
    for triangle in mesh.triangles:
        if len(set(triangle)) != 3 or any(
            not 0 <= index < len(mesh.vertices) for index in triangle
        ):
            raise ArPreviewError("preview_triangle_invalid")
        indices.extend(triangle)
    body = {
        "contract": AR_PREVIEW_CONTRACT,
        "source": {
            "cad_preview_revision_id": preview.revision_id,
            "design_model_revision_id": preview.source_design_model_revision_id,
            "brep_revision_id": preview.source_brep_revision_id,
            "parent_kind": preview.parent_kind,
            "parent_authority_revision_id": preview.parent_authority_revision_id,
            "scale_state": preview.scale_state,
            "coordinate_unit": preview.coordinate_unit,
        },
        "frame": "REALITYKIT_Y_UP_METRES_ORIGIN_BASE_CENTRE",
        "display_scale_basis": display_scale_basis,
        "authority": {
            "class": "AR_VISUAL_REFERENCE_ONLY",
            "physical_accuracy_validation_status": preview.physical_accuracy_validation_status,
            "mold_use_authorized": False,
            "scan_master_replaced": False,
            "on_device_scale_verified": False,
        },
        "positions": positions,
        "indices": indices,
    }
    digest = hashlib.sha256(_canonical(body)).hexdigest()
    return _canonical({**body, "content_sha256": digest})


__all__ = [
    "AR_PREVIEW_CONTRACT",
    "MAX_AR_TRIANGLES",
    "MAX_AR_VERTICES",
    "ArPreviewError",
    "build_ar_preview_package",
]
