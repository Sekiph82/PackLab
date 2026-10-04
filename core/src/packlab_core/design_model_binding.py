"""Immutable captured Scan Master bindings and standalone design authority roots."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .reconstruction import ScaleState
from .scan_master import ScanMasterRevision, mesh_sha256

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_BINDING_PREFIX = "design-model-binding:"
_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class DesignModelBindingError(ValueError):
    """Raised for missing, invalid, stale or unauthorized parent bindings."""


class ParentBindingStatus(StrEnum):
    CURRENT = "CURRENT"
    PINNED_PARENT_MISSING = "PINNED_PARENT_MISSING"
    NEWER_SCAN_MASTER_AVAILABLE = "NEWER_SCAN_MASTER_AVAILABLE"
    NEWER_RECONSTRUCTION_AVAILABLE = "NEWER_RECONSTRUCTION_AVAILABLE"
    NEWER_SCAN_MASTER_AND_RECONSTRUCTION_AVAILABLE = (
        "NEWER_SCAN_MASTER_AND_RECONSTRUCTION_AVAILABLE"
    )


class StandaloneDesignGeometrySourceKind(StrEnum):
    USER_AUTHORED_NOMINAL_DIMENSIONS = "USER_AUTHORED_NOMINAL_DIMENSIONS"
    REFERENCE_DIMENSIONS = "REFERENCE_DIMENSIONS"
    REVIEWED_REUSABLE_TEMPLATE = "REVIEWED_REUSABLE_TEMPLATE"


def _text(value: object, field: str, *, maximum: int = 1000) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 and character not in "\t\n" for character in value)
    ):
        raise DesignModelBindingError(f"{field}_invalid")
    return value


def _utc_timestamp(value: str) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise DesignModelBindingError("created_at_must_be_utc_z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as error:
        raise DesignModelBindingError("created_at_invalid") from error
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise DesignModelBindingError("created_at_must_be_utc_z")


def _parent_facts(scan_master: ScanMasterRevision | None) -> dict[str, object]:
    if not isinstance(scan_master, ScanMasterRevision):
        raise DesignModelBindingError("scan_master_parent_missing")
    manifest = scan_master.manifest
    geometry_digest = mesh_sha256(scan_master.mesh)
    scale_value = manifest.get("scale_state")
    if not isinstance(scale_value, str):
        raise DesignModelBindingError("scan_master_scale_state_invalid")
    try:
        scale_state = ScaleState(scale_value)
    except (KeyError, ValueError, TypeError) as error:
        raise DesignModelBindingError("scan_master_scale_state_invalid") from error
    if (
        manifest.get("scan_master_revision_id") != scan_master.revision_id
        or manifest.get("project_id") != scan_master.project_id
        or manifest.get("authority_class") != "SCAN_MASTER"
        or manifest.get("output_geometry_sha256") != geometry_digest
        or manifest.get("physical_accuracy_validation_status") != _DEFERRED
        or manifest.get("mold_use_authorized") is not False
        or scale_state not in {ScaleState.RELATIVE, ScaleState.METRIC_UNVERIFIED}
    ):
        raise DesignModelBindingError("scan_master_parent_authority_invalid")
    reconstruction_revision = manifest.get("reconstruction_revision_id")
    scale_provenance_id = manifest.get("scale_provenance_id")
    if (
        not isinstance(reconstruction_revision, str)
        or not reconstruction_revision.strip()
        or not isinstance(scale_provenance_id, str)
        or not scale_provenance_id.strip()
    ):
        raise DesignModelBindingError("scan_master_parent_provenance_incomplete")
    return {
        "project_id": scan_master.project_id,
        "scan_master_revision_id": scan_master.revision_id,
        "scan_master_geometry_sha256": geometry_digest,
        "reconstruction_revision_id": reconstruction_revision,
        "scale_state": scale_state,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": _DEFERRED,
        "mold_use_authorized": False,
    }


@dataclass(frozen=True, slots=True)
class DesignModelParentBindingRevision:
    """Metadata revision only; it does not contain or create Design Model geometry."""

    revision_id: str
    project_id: str
    fitted_to_scan_master_revision_id: str
    scan_master_geometry_sha256: str
    reconstruction_revision_id: str
    scale_state: ScaleState
    scale_provenance_id: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    actor_id: str
    reason: str
    created_at_utc: str
    previous_binding_revision_id: str | None = None

    def __post_init__(self) -> None:
        _text(self.project_id, "project_id")
        _text(self.fitted_to_scan_master_revision_id, "scan_master_revision_id")
        if not isinstance(self.scan_master_geometry_sha256, str) or not _SHA256.fullmatch(
            self.scan_master_geometry_sha256
        ):
            raise DesignModelBindingError("scan_master_geometry_digest_invalid")
        _text(self.reconstruction_revision_id, "reconstruction_revision_id")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise DesignModelBindingError("design_model_scale_state_invalid")
        _text(self.scale_provenance_id, "scale_provenance_id")
        if (
            self.physical_accuracy_validation_status != _DEFERRED
            or self.mold_use_authorized is not False
        ):
            raise DesignModelBindingError("design_model_physical_authority_forbidden")
        _text(self.actor_id, "actor_id")
        _text(self.reason, "binding_reason")
        _utc_timestamp(self.created_at_utc)
        if self.previous_binding_revision_id is not None:
            _text(self.previous_binding_revision_id, "previous_binding_revision_id")
        if self.revision_id != _binding_revision_id(
            self.project_id,
            self.fitted_to_scan_master_revision_id,
            self.scan_master_geometry_sha256,
            self.reconstruction_revision_id,
            self.scale_state,
            self.scale_provenance_id,
            self.previous_binding_revision_id,
            self.reason,
        ):
            raise DesignModelBindingError("design_model_binding_revision_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.design-model-parent-binding.v1",
            "revision_id": self.revision_id,
            "project_id": self.project_id,
            "fitted_to_scan_master_revision_id": self.fitted_to_scan_master_revision_id,
            "scan_master_geometry_sha256": self.scan_master_geometry_sha256,
            "reconstruction_revision_id": self.reconstruction_revision_id,
            "scale_state": self.scale_state.value,
            "scale_provenance_id": self.scale_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
            "previous_binding_revision_id": self.previous_binding_revision_id,
        }


@dataclass(frozen=True, slots=True)
class StandaloneDesignGeometryRoot:
    """Immutable design-only root with no Scan Master or captured ancestry."""

    revision_id: str
    content_sha256: str
    project_id: str
    source_kind: StandaloneDesignGeometrySourceKind
    source_provenance_id: str
    scale_state: ScaleState
    coordinate_unit: str
    unit_provenance_id: str
    actor_id: str
    reason: str
    created_at_utc: str
    physical_accuracy_validation_status: str = _DEFERRED
    mold_use_authorized: bool = False
    captured_ancestry_exists: bool = False

    def __post_init__(self) -> None:
        _text(self.project_id, "project_id")
        if not isinstance(self.source_kind, StandaloneDesignGeometrySourceKind):
            raise DesignModelBindingError("standalone_source_kind_invalid")
        _text(self.source_provenance_id, "source_provenance_id")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state not in {
            ScaleState.RELATIVE,
            ScaleState.METRIC_UNVERIFIED,
        }:
            raise DesignModelBindingError("standalone_scale_state_invalid")
        expected_unit = (
            "reconstruction_units" if self.scale_state is ScaleState.RELATIVE else "mm_unverified"
        )
        if self.coordinate_unit != expected_unit:
            raise DesignModelBindingError("standalone_coordinate_unit_mismatch")
        _text(self.unit_provenance_id, "unit_provenance_id")
        _text(self.actor_id, "actor_id")
        why = _text(self.reason, "standalone_root_reason")
        _utc_timestamp(self.created_at_utc)
        if (
            self.physical_accuracy_validation_status != _DEFERRED
            or self.mold_use_authorized is not False
            or self.captured_ancestry_exists is not False
        ):
            raise DesignModelBindingError("standalone_root_authority_forbidden")
        payload = _standalone_root_payload(
            self.project_id,
            self.source_kind,
            self.source_provenance_id,
            self.scale_state,
            self.coordinate_unit,
            self.unit_provenance_id,
            self.actor_id,
            why,
            self.created_at_utc,
        )
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "utf-8"
            )
        ).hexdigest()
        if self.content_sha256 != digest:
            raise DesignModelBindingError("standalone_root_digest_mismatch")
        if self.revision_id != f"standalone-design-geometry:{digest}":
            raise DesignModelBindingError("standalone_root_revision_id_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.standalone-design-geometry-root.v1",
            "authority_class": "STANDALONE_DESIGN_GEOMETRY",
            "revision_id": self.revision_id,
            "content_sha256": self.content_sha256,
            "project_id": self.project_id,
            "source_kind": self.source_kind.value,
            "source_provenance_id": self.source_provenance_id,
            "scale_state": self.scale_state.value,
            "coordinate_unit": self.coordinate_unit,
            "unit_provenance_id": self.unit_provenance_id,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "captured_ancestry_exists": self.captured_ancestry_exists,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "created_at_utc": self.created_at_utc,
        }


def create_standalone_design_geometry_root(
    *,
    project_id: str,
    source_kind: StandaloneDesignGeometrySourceKind,
    source_provenance_id: str,
    scale_state: ScaleState,
    unit_provenance_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> StandaloneDesignGeometryRoot:
    """Create a truthful, versioned model-only design root without captured ancestry."""
    _text(project_id, "project_id")
    if not isinstance(source_kind, StandaloneDesignGeometrySourceKind):
        raise DesignModelBindingError("standalone_source_kind_invalid")
    _text(source_provenance_id, "source_provenance_id")
    if not isinstance(scale_state, ScaleState) or scale_state not in {
        ScaleState.RELATIVE,
        ScaleState.METRIC_UNVERIFIED,
    }:
        raise DesignModelBindingError("standalone_scale_state_invalid")
    _text(unit_provenance_id, "unit_provenance_id")
    _text(actor_id, "actor_id")
    _text(reason, "standalone_root_reason")
    _utc_timestamp(created_at_utc)
    unit = "reconstruction_units" if scale_state is ScaleState.RELATIVE else "mm_unverified"
    payload = _standalone_root_payload(
        project_id,
        source_kind,
        source_provenance_id,
        scale_state,
        unit,
        unit_provenance_id,
        actor_id,
        reason,
        created_at_utc,
    )
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()
    return StandaloneDesignGeometryRoot(
        revision_id=f"standalone-design-geometry:{digest}",
        content_sha256=digest,
        project_id=project_id,
        source_kind=source_kind,
        source_provenance_id=source_provenance_id,
        scale_state=scale_state,
        coordinate_unit=unit,
        unit_provenance_id=unit_provenance_id,
        actor_id=actor_id,
        reason=reason,
        created_at_utc=created_at_utc,
    )


def _standalone_root_payload(
    project_id: str,
    source_kind: StandaloneDesignGeometrySourceKind,
    source_provenance_id: str,
    scale_state: ScaleState,
    coordinate_unit: str,
    unit_provenance_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> dict[str, object]:
    return {
        "contract": "packlab.standalone-design-geometry-root.v1",
        "authority_class": "STANDALONE_DESIGN_GEOMETRY",
        "project_id": project_id,
        "source_kind": source_kind.value,
        "source_provenance_id": source_provenance_id,
        "scale_state": scale_state.value,
        "coordinate_unit": coordinate_unit,
        "unit_provenance_id": unit_provenance_id,
        "physical_accuracy_validation_status": _DEFERRED,
        "mold_use_authorized": False,
        "captured_ancestry_exists": False,
        "actor_id": actor_id,
        "reason": reason,
        "created_at_utc": created_at_utc,
    }


@dataclass(frozen=True, slots=True)
class DesignModelParentStatus:
    status: ParentBindingStatus
    pinned_parent_available: bool
    newer_scan_master_available: bool
    newer_reconstruction_available: bool
    bound_scan_master_revision_id: str
    latest_scan_master_revision_id: str | None
    bound_reconstruction_revision_id: str
    latest_reconstruction_revision_id: str

    @property
    def stale(self) -> bool:
        return self.status is not ParentBindingStatus.CURRENT


def bind_design_model_parent(
    scan_master: ScanMasterRevision | None,
    *,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelParentBindingRevision:
    """Create the initial immutable parent binding for a future Design Model."""

    facts = _parent_facts(scan_master)
    return _make_binding(facts, actor_id, reason, created_at_utc, None)


def rebind_design_model_parent(
    current_binding: DesignModelParentBindingRevision,
    new_scan_master: ScanMasterRevision | None,
    *,
    expected_current_binding_revision_id: str,
    actor_id: str,
    reason: str,
    created_at_utc: str,
) -> DesignModelParentBindingRevision:
    """Return a new binding revision while preserving the old revision unchanged."""

    if not isinstance(current_binding, DesignModelParentBindingRevision):
        raise DesignModelBindingError("current_design_model_binding_required")
    if expected_current_binding_revision_id != current_binding.revision_id:
        raise DesignModelBindingError("design_model_binding_revision_stale")
    facts = _parent_facts(new_scan_master)
    if facts["project_id"] != current_binding.project_id:
        raise DesignModelBindingError("scan_master_parent_project_mismatch")
    if (
        facts["scan_master_revision_id"] == current_binding.fitted_to_scan_master_revision_id
        and facts["scan_master_geometry_sha256"] == current_binding.scan_master_geometry_sha256
    ):
        raise DesignModelBindingError("design_model_rebind_parent_unchanged")
    return _make_binding(facts, actor_id, reason, created_at_utc, current_binding.revision_id)


def inspect_design_model_parent(
    binding: DesignModelParentBindingRevision,
    *,
    available_scan_masters: tuple[ScanMasterRevision, ...],
    latest_scan_master_revision_id: str | None,
    latest_reconstruction_revision_id: str,
) -> DesignModelParentStatus:
    """Report pin availability and newer source revisions without retargeting the binding."""

    if not isinstance(binding, DesignModelParentBindingRevision):
        raise DesignModelBindingError("design_model_binding_required")
    if not isinstance(available_scan_masters, tuple):
        raise DesignModelBindingError("available_scan_masters_must_be_tuple")
    facts = tuple(_parent_facts(item) for item in available_scan_masters)
    if any(item["project_id"] != binding.project_id for item in facts):
        raise DesignModelBindingError("available_scan_master_project_mismatch")
    revision_ids = tuple(str(item["scan_master_revision_id"]) for item in facts)
    if len(set(revision_ids)) != len(revision_ids):
        raise DesignModelBindingError("duplicate_available_scan_master_revision")
    if (
        latest_scan_master_revision_id is not None
        and latest_scan_master_revision_id not in revision_ids
    ):
        raise DesignModelBindingError("latest_scan_master_revision_missing")
    latest_reconstruction = _text(
        latest_reconstruction_revision_id, "latest_reconstruction_revision_id"
    )
    pinned_parent_available = any(
        item["scan_master_revision_id"] == binding.fitted_to_scan_master_revision_id
        and item["scan_master_geometry_sha256"] == binding.scan_master_geometry_sha256
        for item in facts
    )
    newer_scan_master = (
        latest_scan_master_revision_id is not None
        and latest_scan_master_revision_id != binding.fitted_to_scan_master_revision_id
    )
    newer_reconstruction = latest_reconstruction != binding.reconstruction_revision_id
    if not pinned_parent_available:
        status = ParentBindingStatus.PINNED_PARENT_MISSING
    elif newer_scan_master and newer_reconstruction:
        status = ParentBindingStatus.NEWER_SCAN_MASTER_AND_RECONSTRUCTION_AVAILABLE
    elif newer_scan_master:
        status = ParentBindingStatus.NEWER_SCAN_MASTER_AVAILABLE
    elif newer_reconstruction:
        status = ParentBindingStatus.NEWER_RECONSTRUCTION_AVAILABLE
    else:
        status = ParentBindingStatus.CURRENT
    return DesignModelParentStatus(
        status,
        pinned_parent_available,
        newer_scan_master,
        newer_reconstruction,
        binding.fitted_to_scan_master_revision_id,
        latest_scan_master_revision_id,
        binding.reconstruction_revision_id,
        latest_reconstruction,
    )


def _make_binding(
    parent: dict[str, object],
    actor_id: str,
    reason: str,
    created_at_utc: str,
    previous_binding_revision_id: str | None,
) -> DesignModelParentBindingRevision:
    actor = _text(actor_id, "actor_id")
    why = _text(reason, "binding_reason")
    _utc_timestamp(created_at_utc)
    scale_state = parent["scale_state"]
    if not isinstance(scale_state, ScaleState):
        raise DesignModelBindingError("scan_master_scale_state_invalid")
    revision_id = _binding_revision_id(
        str(parent["project_id"]),
        str(parent["scan_master_revision_id"]),
        str(parent["scan_master_geometry_sha256"]),
        str(parent["reconstruction_revision_id"]),
        scale_state,
        str(parent["scale_provenance_id"]),
        previous_binding_revision_id,
        why,
    )
    return DesignModelParentBindingRevision(
        revision_id=revision_id,
        project_id=str(parent["project_id"]),
        fitted_to_scan_master_revision_id=str(parent["scan_master_revision_id"]),
        scan_master_geometry_sha256=str(parent["scan_master_geometry_sha256"]),
        reconstruction_revision_id=str(parent["reconstruction_revision_id"]),
        scale_state=scale_state,
        scale_provenance_id=str(parent["scale_provenance_id"]),
        physical_accuracy_validation_status=_DEFERRED,
        mold_use_authorized=False,
        actor_id=actor,
        reason=why,
        created_at_utc=created_at_utc,
        previous_binding_revision_id=previous_binding_revision_id,
    )


def _binding_revision_id(
    project_id: str,
    scan_master_revision_id: str,
    scan_master_geometry_sha256: str,
    reconstruction_revision_id: str,
    scale_state: ScaleState,
    scale_provenance_id: str,
    previous_binding_revision_id: str | None,
    reason: str,
) -> str:
    identity = {
        "contract": "packlab.design-model-parent-binding.v1",
        "project_id": project_id,
        "fitted_to_scan_master_revision_id": scan_master_revision_id,
        "scan_master_geometry_sha256": scan_master_geometry_sha256,
        "reconstruction_revision_id": reconstruction_revision_id,
        "scale_state": scale_state.value,
        "scale_provenance_id": scale_provenance_id,
        "physical_accuracy_validation_status": _DEFERRED,
        "mold_use_authorized": False,
        "previous_binding_revision_id": previous_binding_revision_id,
        "reason": reason,
    }
    return (
        _BINDING_PREFIX
        + hashlib.sha256(
            json.dumps(identity, sort_keys=True, separators=(",", ":"), allow_nan=False).encode(
                "ascii"
            )
        ).hexdigest()
    )


__all__ = [
    "DesignModelBindingError",
    "DesignModelParentBindingRevision",
    "DesignModelParentStatus",
    "ParentBindingStatus",
    "StandaloneDesignGeometryRoot",
    "StandaloneDesignGeometrySourceKind",
    "bind_design_model_parent",
    "create_standalone_design_geometry_root",
    "inspect_design_model_parent",
    "rebind_design_model_parent",
]
