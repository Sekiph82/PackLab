"""Non-repairing, provenance-bound BREP topology diagnostics."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from .cad_adapter import CadAdapterError, CadTopologySnapshot, inspect_shape_topology
from .cad_brep import CadBrepRepresentationRevision


class CadValidationError(ValueError):
    """Raised when a topology report is requested for an unbound representation."""


@dataclass(frozen=True, slots=True)
class CadBrepValidationReport:
    report_id: str
    status: str
    kernel_valid: bool
    valid_closed_solid: bool
    shell_count: int
    closed_shell_count: int
    solid_count: int
    open_edge_count: int
    nonmanifold_edge_count: int
    invalid_topology_evidence: tuple[str, ...]
    failure_diagnostics: tuple[str, ...]
    source_brep_revision_id: str
    source_design_model_revision_id: str
    source_operation_id: str
    source_input_ids: tuple[str, ...]
    parent_kind: str
    parent_authority_revision_id: str
    scale_state: str
    coordinate_unit: str
    physical_accuracy_validation_status: str
    mold_use_authorized: bool
    repair_performed: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.cad-brep-validation.v1",
            "authority_class": "CAD_TOPOLOGY_DIAGNOSTIC",
            "report_id": self.report_id,
            "status": self.status,
            "kernel_valid": self.kernel_valid,
            "valid_closed_solid": self.valid_closed_solid,
            "shell_count": self.shell_count,
            "closed_shell_count": self.closed_shell_count,
            "solid_count": self.solid_count,
            "open_edge_count": self.open_edge_count,
            "nonmanifold_edge_count": self.nonmanifold_edge_count,
            "invalid_topology_evidence": list(self.invalid_topology_evidence),
            "failure_diagnostics": list(self.failure_diagnostics),
            "source_brep_revision_id": self.source_brep_revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "source_operation_id": self.source_operation_id,
            "source_input_ids": list(self.source_input_ids),
            "parent_authority": {
                "kind": self.parent_kind,
                "revision_id": self.parent_authority_revision_id,
            },
            "scale_state": self.scale_state,
            "coordinate_unit": self.coordinate_unit,
            "physical_accuracy_validation_status": self.physical_accuracy_validation_status,
            "mold_use_authorized": self.mold_use_authorized,
            "repair_performed": self.repair_performed,
            "physical_accuracy_inferred": False,
            "manufacturing_suitability_inferred": False,
        }


def validate_cad_brep(
    representation: CadBrepRepresentationRevision,
) -> CadBrepValidationReport:
    """Report topology and source binding for one BREP; never repair the shape."""
    if not isinstance(representation, CadBrepRepresentationRevision):
        raise CadValidationError("cad_brep_representation_required")
    handle = representation.shape_handle
    if (
        representation.source_design_model_revision_id != handle.source_design_model_revision_id
        or representation.parent_kind is not handle.parent_kind
        or representation.parent_authority_revision_id != handle.parent_authority_revision_id
        or representation.scale_state is not handle.scale_state
        or representation.coordinate_unit != handle.coordinate_unit
        or representation.physical_accuracy_validation_status != "DEFERRED_OWNER_VALIDATION"
        or representation.mold_use_authorized
    ):
        raise CadValidationError("cad_brep_shape_provenance_mismatch")
    try:
        snapshot = inspect_shape_topology(handle)
        evidence = _snapshot_evidence(snapshot)
        kernel_valid = snapshot.kernel_valid
        solid_count = snapshot.solid_count
        shell_count = snapshot.shell_count
        closed_shell_count = snapshot.closed_shell_count
        open_edge_count = snapshot.open_edge_count
        nonmanifold_edge_count = snapshot.nonmanifold_edge_count
        valid_closed_solid = (
            kernel_valid
            and solid_count == 1
            and shell_count > 0
            and closed_shell_count == shell_count
            and open_edge_count == 0
            and nonmanifold_edge_count == 0
        )
        diagnostics = _failure_codes(
            kernel_valid,
            solid_count,
            shell_count,
            closed_shell_count,
            open_edge_count,
            nonmanifold_edge_count,
        )
        status = "VALID" if valid_closed_solid else "INVALID"
    except CadAdapterError as error:
        kernel_valid = False
        valid_closed_solid = False
        solid_count = shell_count = closed_shell_count = open_edge_count = 0
        nonmanifold_edge_count = 0
        evidence = ()
        diagnostics = (str(error),)
        status = "FAILED"
    except Exception as error:
        kernel_valid = False
        valid_closed_solid = False
        solid_count = shell_count = closed_shell_count = open_edge_count = 0
        nonmanifold_edge_count = 0
        evidence = ()
        diagnostics = (f"cad_topology_inspection_failed:{type(error).__name__}",)
        status = "FAILED"
    payload = "|".join(
        (
            "packlab.cad-brep-validation.v1",
            representation.revision_id,
            status,
            str(kernel_valid),
            str(valid_closed_solid),
            str(shell_count),
            str(closed_shell_count),
            str(solid_count),
            str(open_edge_count),
            str(nonmanifold_edge_count),
            *evidence,
            *diagnostics,
        )
    )
    report_id = "cad-validation:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return CadBrepValidationReport(
        report_id,
        status,
        kernel_valid,
        valid_closed_solid,
        shell_count,
        closed_shell_count,
        solid_count,
        open_edge_count,
        nonmanifold_edge_count,
        evidence,
        diagnostics,
        representation.revision_id,
        representation.source_design_model_revision_id,
        representation.source_operation_id,
        representation.source_input_ids,
        representation.parent_kind.value,
        representation.parent_authority_revision_id,
        representation.scale_state.value,
        representation.coordinate_unit,
        representation.physical_accuracy_validation_status,
        representation.mold_use_authorized,
    )


def _snapshot_evidence(snapshot: CadTopologySnapshot) -> tuple[str, ...]:
    return snapshot.invalid_statuses


def _failure_codes(
    kernel_valid: bool,
    solid_count: int,
    shell_count: int,
    closed_shell_count: int,
    open_edge_count: int,
    nonmanifold_edge_count: int,
) -> tuple[str, ...]:
    codes: list[str] = []
    if not kernel_valid:
        codes.append("kernel_reports_invalid_topology")
    if solid_count != 1:
        codes.append("single_solid_required")
    if shell_count == 0:
        codes.append("shell_missing")
    if closed_shell_count != shell_count:
        codes.append("open_shell_detected")
    if open_edge_count:
        codes.append("open_or_free_edge_detected")
    if nonmanifold_edge_count:
        codes.append("nonmanifold_edge_detected")
    return tuple(codes)


__all__ = ["CadBrepValidationReport", "CadValidationError", "validate_cad_brep"]
