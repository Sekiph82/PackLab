"""Authority limits shared by flexible-pack reports and metadata handoffs."""

from __future__ import annotations

from .design_model import DesignModelParentKind, DesignModelRevision, PackageFamily

_DESIGN_TARGETS = {"DESIGN_MODEL", "PREVIEW_PROXY", "DESIGN_MODEL_WITH_PREVIEW_PROXY"}
_LIMITATIONS = (
    "design_geometry_only",
    "flexible_film_deformation_not_measured",
    "physical_accuracy_validation_deferred",
    "no_mold_or_manufacturing_authority",
    "no_certified_volume_or_physical_tolerance_claim",
    "no_scan_master_promotion",
)


class FlexiblePackAuthorityError(ValueError):
    """Raised when flexible-pack geometry is used beyond design/preview authority."""


def is_flexible_pack_model(model: object) -> bool:
    if not isinstance(model, DesignModelRevision):
        return False
    return model.package_family in {PackageFamily.TUBE, PackageFamily.FLEXIBLE_PACK} or any(
        parameter.parameter_id.startswith("pouch_") for parameter in model.parameters
    )


def flexible_pack_authority_handoff(
    model: DesignModelRevision,
    *,
    requested_authority: str = "DESIGN_MODEL_WITH_PREVIEW_PROXY",
) -> dict[str, object]:
    """Return deterministic report/export metadata or reject authority promotion."""
    if not is_flexible_pack_model(model):
        raise FlexiblePackAuthorityError("flexible_pack_design_model_required")
    if not isinstance(requested_authority, str) or requested_authority not in _DESIGN_TARGETS:
        raise FlexiblePackAuthorityError("flexible_pack_authority_promotion_forbidden")
    if model.parent_kind is DesignModelParentKind.STANDALONE_DESIGN_GEOMETRY:
        root = model.standalone_root
        if root is None:
            raise FlexiblePackAuthorityError("flexible_pack_parent_authority_invalid")
        parent_authority: dict[str, object] = {
            "kind": DesignModelParentKind.STANDALONE_DESIGN_GEOMETRY.value,
            "root_revision_id": root.revision_id,
            "source_kind": root.source_kind.value,
            "captured_ancestry_exists": False,
        }
    else:
        if (
            model.parent_binding_revision_id is None
            or model.fitted_to_scan_master_revision_id is None
            or model.scan_master_geometry_sha256 is None
        ):
            raise FlexiblePackAuthorityError("flexible_pack_parent_authority_invalid")
        parent_authority = {
            "kind": DesignModelParentKind.CAPTURED_SCAN_MASTER.value,
            "parent_binding_revision_id": model.parent_binding_revision_id,
            "scan_master_revision_id": model.fitted_to_scan_master_revision_id,
            "scan_master_geometry_sha256": model.scan_master_geometry_sha256,
            "captured_ancestry_exists": True,
        }
    return {
        "contract": "packlab.flexible-pack-authority-handoff.v1",
        "design_model_revision_id": model.revision_id,
        "package_family": model.package_family.value,
        "requested_authority": requested_authority,
        "parent_authority": parent_authority,
        "scale_state": model.scale_state.value,
        "coordinate_unit": model.coordinate_unit,
        "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        "preview_authority_class": "PREVIEW_PROXY",
        "metadata_only_handoff": True,
        "scan_master_promotion_allowed": False,
        "captured_geometry_authority": False,
        "mold_use_authorized": False,
        "manufacturing_authority": False,
        "certified_volume_claimed": False,
        "physical_tolerance_claimed": False,
        "limitations": list(_LIMITATIONS),
    }


__all__ = [
    "FlexiblePackAuthorityError",
    "flexible_pack_authority_handoff",
    "is_flexible_pack_model",
]
