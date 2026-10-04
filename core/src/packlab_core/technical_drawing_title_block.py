"""Privacy-safe, deterministic technical drawing title-block data."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass

from . import __version__ as PACKLAB_VERSION
from .cad_adapter import (
    CAD_BINDING_PACKAGE,
    CAD_RUNTIME_VERSION_STATUS_OBSERVED,
    CadRuntimeDiagnostics,
    CadRuntimeStatus,
)
from .cad_brep import CadBrepRepresentationRevision
from .cad_validation import validate_cad_brep
from .design_model import DesignModelRevision
from .reconstruction import ScaleState

TITLE_BLOCK_CONTRACT = "packlab.technical-drawing-title-block.v1"
_VIEW_ID = re.compile(r"^[A-Z][A-Z0-9_.:@-]{0,63}$")


class DrawingTitleBlockError(ValueError):
    """Raised when title-block source authority or version evidence is incomplete."""


@dataclass(frozen=True, slots=True)
class TechnicalDrawingTitleBlock:
    revision_id: str
    project_id: str
    package_family: str
    design_model_revision_id: str
    cad_representation_revision_id: str
    cad_geometry_sha256: str
    parent_kind: str
    parent_authority_revision_id: str
    drawing_revision_id: str
    coordinate_unit: str
    scale_state: str
    packlab_version: str
    binding_package: str
    binding_version: str
    kernel_version: str
    generated_view_ids: tuple[str, ...]
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    disclaimer: str
    generated_at_utc: str | None
    contract: str = TITLE_BLOCK_CONTRACT

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "DERIVED_TECHNICAL_DRAWING_TITLE_BLOCK",
            "title_block_revision_id": self.revision_id,
            "package": {
                "project_id": self.project_id,
                "family": self.package_family,
            },
            "source": {
                "design_model_revision_id": self.design_model_revision_id,
                "cad_representation_revision_id": self.cad_representation_revision_id,
                "cad_geometry_sha256": self.cad_geometry_sha256,
                "parent_authority": {
                    "kind": self.parent_kind,
                    "revision_id": self.parent_authority_revision_id,
                },
            },
            "drawing_revision_id": self.drawing_revision_id,
            "units": {
                "coordinate_unit": self.coordinate_unit,
                "scale_state": self.scale_state,
            },
            "software_versions": {
                "packlab": self.packlab_version,
                "python_cad_binding": {
                    "package": self.binding_package,
                    "version": self.binding_version,
                },
                "occt_kernel": self.kernel_version,
            },
            "generated_views": list(self.generated_view_ids),
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "authority_disclaimer": self.disclaimer,
            "presentation_metadata": (
                {"generated_at_utc": self.generated_at_utc}
                if self.generated_at_utc is not None
                else {}
            ),
            "machine_identity_included": False,
            "ambient_paths_included": False,
            "certification_claimed": False,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
            "scan_master_promoted": False,
            "design_model_replaced": False,
            "cad_brep_replaced": False,
        }


def build_technical_drawing_title_block(
    model: DesignModelRevision,
    representation: CadBrepRepresentationRevision,
    diagnostics: CadRuntimeDiagnostics,
    *,
    generated_view_ids: tuple[str, ...],
    generated_at_utc: str | None = None,
) -> TechnicalDrawingTitleBlock:
    """Bind the drawing header to exact CAD/model authority and observed versions."""
    if not isinstance(model, DesignModelRevision):
        raise DrawingTitleBlockError("design_model_revision_required")
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise DrawingTitleBlockError("cad_brep_representation_required")
    if not isinstance(diagnostics, CadRuntimeDiagnostics):
        raise DrawingTitleBlockError("cad_runtime_diagnostics_required")
    parent_revision = (
        model.standalone_root.revision_id
        if model.standalone_root is not None
        else model.parent_binding_revision_id
    )
    if (
        parent_revision is None
        or representation.source_design_model_revision_id != model.revision_id
        or representation.parent_kind is not model.parent_kind
        or representation.parent_authority_revision_id != parent_revision
        or representation.scale_state is not model.scale_state
        or representation.coordinate_unit != model.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized is not False
        or model.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or model.mold_use_authorized is not False
    ):
        raise DrawingTitleBlockError("drawing_title_block_source_authority_mismatch")
    try:
        validation = validate_cad_brep(representation)
        if not validation.valid_closed_solid:
            raise DrawingTitleBlockError("drawing_title_block_valid_brep_required")
    except DrawingTitleBlockError:
        raise
    except Exception as error:
        raise DrawingTitleBlockError("drawing_title_block_brep_validation_failed") from error
    if (
        diagnostics.status is not CadRuntimeStatus.READY
        or diagnostics.binding_package != CAD_BINDING_PACKAGE
        or not isinstance(diagnostics.binding_version, str)
        or not diagnostics.binding_version.strip()
        or diagnostics.binding_version_status != CAD_RUNTIME_VERSION_STATUS_OBSERVED
        or not isinstance(diagnostics.kernel_version, str)
        or not diagnostics.kernel_version.strip()
        or diagnostics.kernel_version_status != CAD_RUNTIME_VERSION_STATUS_OBSERVED
    ):
        raise DrawingTitleBlockError("drawing_title_block_software_versions_unobserved")
    if (
        not isinstance(generated_view_ids, tuple)
        or not generated_view_ids
        or len(generated_view_ids) > 32
        or any(
            not isinstance(view_id, str) or not _VIEW_ID.fullmatch(view_id)
            for view_id in generated_view_ids
        )
        or len(set(generated_view_ids)) != len(generated_view_ids)
    ):
        raise DrawingTitleBlockError("drawing_title_block_generated_views_invalid")
    views = tuple(sorted(generated_view_ids))
    if generated_at_utc is not None and not _valid_utc_timestamp(generated_at_utc):
        raise DrawingTitleBlockError("drawing_title_block_timestamp_invalid")

    disclaimer = (
        "Numerical millimetres are unverified against the physical benchmark; this drawing is not mold or manufacturing approval."
        if model.scale_state is ScaleState.METRIC_UNVERIFIED
        else "Dimensions are reconstruction-relative, not millimetres; this drawing is not physical metrology or mold/manufacturing approval."
    )
    identity = {
        "project_id": model.project_id,
        "package_family": model.package_family.value,
        "design_model_revision_id": model.revision_id,
        "cad_representation_revision_id": representation.revision_id,
        "cad_geometry_sha256": representation.geometry_sha256,
        "parent_kind": model.parent_kind.value,
        "parent_authority_revision_id": parent_revision,
        "coordinate_unit": model.coordinate_unit,
        "scale_state": model.scale_state.value,
        "packlab_version": PACKLAB_VERSION,
        "binding_package": diagnostics.binding_package,
        "binding_version": diagnostics.binding_version,
        "kernel_version": diagnostics.kernel_version,
        "generated_view_ids": views,
        "disclaimer": disclaimer,
    }
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
    ).hexdigest()
    return TechnicalDrawingTitleBlock(
        revision_id=f"drawing-title-block:{digest}",
        project_id=model.project_id,
        package_family=model.package_family.value,
        design_model_revision_id=model.revision_id,
        cad_representation_revision_id=representation.revision_id,
        cad_geometry_sha256=representation.geometry_sha256,
        parent_kind=model.parent_kind.value,
        parent_authority_revision_id=parent_revision,
        drawing_revision_id=f"drawing-revision:{digest}",
        coordinate_unit=model.coordinate_unit,
        scale_state=model.scale_state.value,
        packlab_version=PACKLAB_VERSION,
        binding_package=diagnostics.binding_package,
        binding_version=diagnostics.binding_version,
        kernel_version=diagnostics.kernel_version,
        generated_view_ids=views,
        physical_accuracy_validation_status=model.physical_accuracy_validation_status,
        mold_use_authorized=model.mold_use_authorized,
        disclaimer=disclaimer,
        generated_at_utc=generated_at_utc,
    )


def _valid_utc_timestamp(value: str) -> bool:
    if not isinstance(value, str) or not value.endswith("Z"):
        return False
    try:
        from datetime import datetime

        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError:
        return False
    offset = parsed.utcoffset()
    return offset is not None and offset.total_seconds() == 0


__all__ = [
    "TITLE_BLOCK_CONTRACT",
    "DrawingTitleBlockError",
    "TechnicalDrawingTitleBlock",
    "build_technical_drawing_title_block",
]
