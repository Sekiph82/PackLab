"""Canonical persistence boundary for component visual-material assignments."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any

from .component_visual_assignments import (
    ComponentVisualAssignmentState,
    ContentAppearanceAssignmentRevision,
    GeometryMaterialAssignmentRevision,
    create_component_visual_assignment_state,
)
from .design_model import DesignModelRevision
from .pcr_material_declarations import (
    ExternalAuthorityReference,
    PCRDeclarationRevision,
    PCRDeclarationStatus,
    PCRVisualVariantRevision,
)
from .visual_material_library import (
    MaterialSourceClass,
    VisualMaterialLibraryRevision,
)

COMPONENT_MATERIAL_PROJECT_CONTRACT = "packlab.component-material-project.v1"
COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION = 1
MAX_COMPONENT_MATERIAL_PROJECT_BYTES = 8 * 1024 * 1024


class ComponentMaterialProjectError(ValueError):
    """Raised when component material project data is stale or malformed."""


@dataclass(frozen=True, slots=True)
class ComponentMaterialProjectEntry:
    component_id: str
    visual_state: ComponentVisualAssignmentState
    pcr_declaration: PCRDeclarationRevision | None = None
    pcr_visual_variants: tuple[PCRVisualVariantRevision, ...] = ()

    def __post_init__(self) -> None:
        if (
            not isinstance(self.component_id, str)
            or not isinstance(self.visual_state, ComponentVisualAssignmentState)
            or self.visual_state.component_id != self.component_id
            or not isinstance(self.pcr_visual_variants, tuple)
            or any(
                not isinstance(item, PCRVisualVariantRevision) for item in self.pcr_visual_variants
            )
        ):
            raise ComponentMaterialProjectError("component_material_entry_invalid")
        if self.pcr_declaration is not None:
            if not isinstance(self.pcr_declaration, PCRDeclarationRevision):
                raise ComponentMaterialProjectError("pcr_declaration_invalid")
            if (
                self.pcr_declaration.design_model_revision_id
                != self.visual_state.source_design_model_revision_id
                or self.pcr_declaration.component_id != self.component_id
            ):
                raise ComponentMaterialProjectError("pcr_declaration_provenance_mismatch")
        variant_ids = tuple(item.variant_id for item in self.pcr_visual_variants)
        if len(variant_ids) != len(set(variant_ids)) or variant_ids != tuple(sorted(variant_ids)):
            raise ComponentMaterialProjectError("pcr_visual_variant_order_or_duplicate_invalid")
        for variant in self.pcr_visual_variants:
            if (
                self.pcr_declaration is None
                or variant.declaration_revision_id != self.pcr_declaration.revision_id
                or variant.material_id != self.pcr_declaration.material_id
                or variant.design_model_revision_id
                != self.visual_state.source_design_model_revision_id
                or variant.component_id != self.component_id
            ):
                raise ComponentMaterialProjectError("pcr_visual_variant_provenance_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "component_id": self.component_id,
            "visual_state": self.visual_state.as_dict(),
            "pcr_declaration": (
                self.pcr_declaration.as_dict() if self.pcr_declaration is not None else None
            ),
            "pcr_visual_variants": [item.as_dict() for item in self.pcr_visual_variants],
        }


@dataclass(frozen=True, slots=True)
class ComponentMaterialProjectDocument:
    revision_id: str
    design_model_revision_id: str
    entries: tuple[ComponentMaterialProjectEntry, ...]
    contract: str = COMPONENT_MATERIAL_PROJECT_CONTRACT
    schema_version: int = COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.contract != COMPONENT_MATERIAL_PROJECT_CONTRACT
            or isinstance(self.schema_version, bool)
            or not isinstance(self.schema_version, int)
            or self.schema_version != COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION
            or not isinstance(self.design_model_revision_id, str)
            or not self.design_model_revision_id
            or not isinstance(self.entries, tuple)
            or any(not isinstance(item, ComponentMaterialProjectEntry) for item in self.entries)
        ):
            raise ComponentMaterialProjectError("component_material_project_invalid")
        component_ids = tuple(item.component_id for item in self.entries)
        if component_ids != tuple(sorted(component_ids)):
            raise ComponentMaterialProjectError("component_material_project_order_invalid")
        if len(component_ids) != len(set(component_ids)):
            raise ComponentMaterialProjectError("component_material_project_component_ambiguous")
        if any(
            item.visual_state.source_design_model_revision_id != self.design_model_revision_id
            for item in self.entries
        ):
            raise ComponentMaterialProjectError("component_material_project_model_mismatch")
        if self.revision_id != "component-material-project:" + _digest(_document_identity(self)):
            raise ComponentMaterialProjectError("component_material_project_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "schema_version": self.schema_version,
            "revision_id": self.revision_id,
            "design_model_revision_id": self.design_model_revision_id,
            "entries": [item.as_dict() for item in self.entries],
            "authority_semantics": "NON_CERTIFIED_VISUAL_ASSIGNMENTS",
            "mutates_design_model": False,
            "physical_or_regulatory_claim": False,
        }

    def canonical_bytes(self) -> bytes:
        body = self.as_dict()
        envelope = {"body": body, "content_sha256": _digest(body)}
        encoded = _canonical_json(envelope)
        if len(encoded) > MAX_COMPONENT_MATERIAL_PROJECT_BYTES:
            raise ComponentMaterialProjectError("component_material_project_size_limit_exceeded")
        return encoded


def create_component_material_project(
    model: DesignModelRevision,
    library: VisualMaterialLibraryRevision,
    entries: tuple[ComponentMaterialProjectEntry, ...],
) -> ComponentMaterialProjectDocument:
    """Build a normalized project snapshot after exact model and library resolution."""
    if not isinstance(model, DesignModelRevision):
        raise ComponentMaterialProjectError("design_model_revision_required")
    if not isinstance(library, VisualMaterialLibraryRevision):
        raise ComponentMaterialProjectError("visual_material_library_required")
    if not isinstance(entries, tuple) or any(
        not isinstance(item, ComponentMaterialProjectEntry) for item in entries
    ):
        raise ComponentMaterialProjectError("component_material_entries_must_be_tuple")
    normalized = tuple(sorted(entries, key=lambda item: item.component_id))
    _validate_entries(model, library, normalized)
    provisional = object.__new__(ComponentMaterialProjectDocument)
    object.__setattr__(provisional, "revision_id", "")
    object.__setattr__(provisional, "design_model_revision_id", model.revision_id)
    object.__setattr__(provisional, "entries", normalized)
    object.__setattr__(provisional, "contract", COMPONENT_MATERIAL_PROJECT_CONTRACT)
    object.__setattr__(provisional, "schema_version", COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION)
    return ComponentMaterialProjectDocument(
        revision_id="component-material-project:" + _digest(_document_identity(provisional)),
        design_model_revision_id=model.revision_id,
        entries=normalized,
    )


def replace_component_material_project_entry(
    document: ComponentMaterialProjectDocument,
    model: DesignModelRevision,
    library: VisualMaterialLibraryRevision,
    entry: ComponentMaterialProjectEntry,
) -> ComponentMaterialProjectDocument:
    """Return a new snapshot with one component replaced; prior bytes remain immutable."""
    _require_document_model(document, model)
    if not isinstance(entry, ComponentMaterialProjectEntry):
        raise ComponentMaterialProjectError("component_material_entry_invalid")
    retained = tuple(item for item in document.entries if item.component_id != entry.component_id)
    return create_component_material_project(model, library, (*retained, entry))


def remove_component_material_project_entry(
    document: ComponentMaterialProjectDocument,
    model: DesignModelRevision,
    library: VisualMaterialLibraryRevision,
    component_id: str,
) -> ComponentMaterialProjectDocument:
    """Return a new snapshot without the exact component entry."""
    _require_document_model(document, model)
    matches = tuple(item for item in document.entries if item.component_id == component_id)
    if len(matches) != 1:
        reason = (
            "component_material_project_component_ambiguous"
            if matches
            else ("component_material_project_component_missing")
        )
        raise ComponentMaterialProjectError(reason)
    remaining = tuple(item for item in document.entries if item.component_id != component_id)
    return create_component_material_project(model, library, remaining)


def deserialize_component_material_project(
    data: bytes | str,
    model: DesignModelRevision,
    library: VisualMaterialLibraryRevision,
) -> ComponentMaterialProjectDocument:
    """Load a canonical v1 snapshot only against its exact active Design Model and library."""
    if not isinstance(model, DesignModelRevision):
        raise ComponentMaterialProjectError("design_model_revision_required")
    if not isinstance(library, VisualMaterialLibraryRevision):
        raise ComponentMaterialProjectError("visual_material_library_required")
    if isinstance(data, bytes):
        raw = data
    elif isinstance(data, str):
        try:
            raw = data.encode("utf-8")
        except UnicodeEncodeError as error:
            raise ComponentMaterialProjectError(
                "component_material_project_encoding_invalid"
            ) from error
    else:
        raise ComponentMaterialProjectError("component_material_project_data_type_invalid")
    if not raw or len(raw) > MAX_COMPONENT_MATERIAL_PROJECT_BYTES:
        raise ComponentMaterialProjectError("component_material_project_size_invalid")
    try:
        envelope = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ComponentMaterialProjectError(f"component_material_project_nonfinite:{value}")
            ),
        )
    except ComponentMaterialProjectError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ComponentMaterialProjectError("component_material_project_json_invalid") from error
    envelope = _mapping(envelope, {"body", "content_sha256"}, "envelope")
    body = _mapping(
        envelope["body"],
        {
            "contract",
            "schema_version",
            "revision_id",
            "design_model_revision_id",
            "entries",
            "authority_semantics",
            "mutates_design_model",
            "physical_or_regulatory_claim",
        },
        "body",
    )
    if body["contract"] != COMPONENT_MATERIAL_PROJECT_CONTRACT:
        raise ComponentMaterialProjectError("component_material_project_contract_unsupported")
    if (
        isinstance(body["schema_version"], bool)
        or not isinstance(body["schema_version"], int)
        or body["schema_version"] != COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION
    ):
        raise ComponentMaterialProjectError("component_material_project_schema_version_unsupported")
    if (
        envelope["content_sha256"] != _digest(body)
        or body["authority_semantics"] != "NON_CERTIFIED_VISUAL_ASSIGNMENTS"
        or body["mutates_design_model"] is not False
        or body["physical_or_regulatory_claim"] is not False
    ):
        raise ComponentMaterialProjectError(
            "component_material_project_integrity_or_authority_invalid"
        )
    model_revision_id = _string(body["design_model_revision_id"], "design_model_revision_id")
    if model_revision_id != model.revision_id:
        raise ComponentMaterialProjectError("component_material_project_design_model_stale")
    raw_entries = _array(body["entries"], "entries")
    entries = tuple(_deserialize_entry(item) for item in raw_entries)
    document = create_component_material_project(model, library, entries)
    if document.revision_id != body["revision_id"] or document.as_dict() != body:
        raise ComponentMaterialProjectError(
            "component_material_project_revision_or_content_mismatch"
        )
    return document


def _validate_entries(
    model: DesignModelRevision,
    library: VisualMaterialLibraryRevision,
    entries: tuple[ComponentMaterialProjectEntry, ...],
) -> None:
    component_ids = {feature.component_id for feature in model.features}
    material_ids = {item.material_id for item in library.materials}
    for entry in entries:
        if entry.component_id not in component_ids:
            raise ComponentMaterialProjectError(
                "component_material_project_component_stale_or_deleted"
            )
        state = entry.visual_state
        if state.source_design_model_revision_id != model.revision_id:
            raise ComponentMaterialProjectError("component_material_project_design_model_stale")
        geometry = state.geometry_material_assignment
        if geometry is not None and (
            geometry.material_library_revision_id != library.revision_id
            or geometry.material_id not in material_ids
        ):
            raise ComponentMaterialProjectError(
                "component_material_project_material_reference_stale"
            )
        declaration = entry.pcr_declaration
        if declaration is not None:
            if declaration.design_model_revision_id != model.revision_id:
                raise ComponentMaterialProjectError("pcr_declaration_design_model_stale")
            if declaration.material_id not in material_ids:
                raise ComponentMaterialProjectError("pcr_declaration_material_reference_stale")
            if geometry is not None and geometry.material_id != declaration.material_id:
                raise ComponentMaterialProjectError("pcr_declaration_material_assignment_mismatch")
        for variant in entry.pcr_visual_variants:
            if variant.design_model_revision_id != model.revision_id:
                raise ComponentMaterialProjectError("pcr_visual_variant_design_model_stale")


def _require_document_model(
    document: ComponentMaterialProjectDocument, model: DesignModelRevision
) -> None:
    if not isinstance(document, ComponentMaterialProjectDocument):
        raise ComponentMaterialProjectError("component_material_project_required")
    if not isinstance(model, DesignModelRevision):
        raise ComponentMaterialProjectError("design_model_revision_required")
    if document.design_model_revision_id != model.revision_id:
        raise ComponentMaterialProjectError("component_material_project_design_model_stale")


def _document_identity(document: ComponentMaterialProjectDocument) -> dict[str, object]:
    return {
        "contract": COMPONENT_MATERIAL_PROJECT_CONTRACT,
        "schema_version": COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION,
        "design_model_revision_id": document.design_model_revision_id,
        "entries": [item.as_dict() for item in document.entries],
    }


def _deserialize_entry(value: object) -> ComponentMaterialProjectEntry:
    raw = _mapping(
        value,
        {"component_id", "visual_state", "pcr_declaration", "pcr_visual_variants"},
        "entry",
    )
    component_id = _string(raw["component_id"], "entry.component_id")
    visual_state = _deserialize_visual_state(raw["visual_state"])
    declaration = (
        _deserialize_pcr_declaration(raw["pcr_declaration"])
        if raw["pcr_declaration"] is not None
        else None
    )
    variants = tuple(
        _deserialize_pcr_variant(item)
        for item in _array(raw["pcr_visual_variants"], "entry.pcr_visual_variants")
    )
    entry = ComponentMaterialProjectEntry(component_id, visual_state, declaration, variants)
    if entry.as_dict() != raw:
        raise ComponentMaterialProjectError("component_material_entry_content_invalid")
    return entry


def _deserialize_visual_state(value: object) -> ComponentVisualAssignmentState:
    raw = _mapping(
        value,
        {
            "contract",
            "authority_class",
            "revision_id",
            "source_design_model_revision_id",
            "component_id",
            "geometry_material_assignment",
            "content_appearance_assignment",
            "geometry_and_content_channels_independent",
            "fill_volume_inferred",
            "formulation_inferred",
            "mutates_design_model",
        },
        "visual_state",
    )
    if (
        raw["geometry_and_content_channels_independent"] is not True
        or raw["fill_volume_inferred"] is not False
        or raw["formulation_inferred"] is not False
        or raw["mutates_design_model"] is not False
    ):
        raise ComponentMaterialProjectError("visual_state_authority_invalid")
    geometry = (
        _deserialize_geometry_assignment(raw["geometry_material_assignment"])
        if raw["geometry_material_assignment"] is not None
        else None
    )
    content = (
        _deserialize_content_assignment(raw["content_appearance_assignment"])
        if raw["content_appearance_assignment"] is not None
        else None
    )
    try:
        state = create_component_visual_assignment_state(geometry, content)
    except ValueError as error:
        raise ComponentMaterialProjectError("visual_state_assignment_invalid") from error
    if state.as_dict() != raw:
        raise ComponentMaterialProjectError("visual_state_content_invalid")
    return state


def _deserialize_geometry_assignment(value: object) -> GeometryMaterialAssignmentRevision:
    raw = _mapping(
        value,
        {
            "contract",
            "authority_class",
            "revision_id",
            "source_design_model_revision_id",
            "component_id",
            "material_library_revision_id",
            "material_id",
            "status",
            "previous_revision_id",
            "authority_semantics",
            "mutates_design_model",
            "physical_or_regulatory_claim",
        },
        "geometry_assignment",
    )
    if (
        raw["authority_class"] != "VISUAL_GEOMETRY_MATERIAL_ASSIGNMENT"
        or raw["authority_semantics"] != "NON_CERTIFIED_VISUAL_REFERENCE"
        or raw["mutates_design_model"] is not False
        or raw["physical_or_regulatory_claim"] is not False
    ):
        raise ComponentMaterialProjectError("geometry_assignment_authority_invalid")
    try:
        assignment = GeometryMaterialAssignmentRevision(
            revision_id=_string(raw["revision_id"], "geometry.revision_id"),
            source_design_model_revision_id=_string(
                raw["source_design_model_revision_id"], "geometry.design_model_revision_id"
            ),
            component_id=_string(raw["component_id"], "geometry.component_id"),
            material_library_revision_id=_optional_string(
                raw["material_library_revision_id"], "geometry.material_library_revision_id"
            ),
            material_id=_optional_string(raw["material_id"], "geometry.material_id"),
            status=_string(raw["status"], "geometry.status"),
            previous_revision_id=_optional_string(
                raw["previous_revision_id"], "geometry.previous_revision_id"
            ),
        )
    except ValueError as error:
        raise ComponentMaterialProjectError("geometry_assignment_invalid") from error
    if assignment.as_dict() != raw:
        raise ComponentMaterialProjectError("geometry_assignment_content_invalid")
    return assignment


def _deserialize_content_assignment(value: object) -> ContentAppearanceAssignmentRevision:
    raw = _mapping(
        value,
        {
            "contract",
            "authority_class",
            "revision_id",
            "source_design_model_revision_id",
            "component_id",
            "display_name",
            "display_color_rgba",
            "opacity_factor",
            "source_classification",
            "status",
            "previous_revision_id",
            "authority_semantics",
            "fill_volume_inferred",
            "formulation_inferred",
            "physical_or_regulatory_claim",
            "mutates_design_model",
        },
        "content_assignment",
    )
    if (
        raw["authority_class"] != "VISUAL_PRODUCT_CONTENT_APPEARANCE_ASSIGNMENT"
        or raw["authority_semantics"] != "NON_CERTIFIED_VISUAL_REFERENCE"
        or raw["fill_volume_inferred"] is not False
        or raw["formulation_inferred"] is not False
        or raw["physical_or_regulatory_claim"] is not False
        or raw["mutates_design_model"] is not False
    ):
        raise ComponentMaterialProjectError("content_assignment_authority_invalid")
    color_raw = raw["display_color_rgba"]
    color = None if color_raw is None else tuple(_number_array(color_raw, 4, "content.color"))
    source_raw = raw["source_classification"]
    try:
        source = MaterialSourceClass(source_raw) if source_raw is not None else None
        assignment = ContentAppearanceAssignmentRevision(
            revision_id=_string(raw["revision_id"], "content.revision_id"),
            source_design_model_revision_id=_string(
                raw["source_design_model_revision_id"], "content.design_model_revision_id"
            ),
            component_id=_string(raw["component_id"], "content.component_id"),
            display_name=_optional_string(raw["display_name"], "content.display_name"),
            display_color_rgba=color,  # type: ignore[arg-type]
            opacity_factor=_optional_number(raw["opacity_factor"], "content.opacity_factor"),
            source_classification=source,
            status=_string(raw["status"], "content.status"),
            previous_revision_id=_optional_string(
                raw["previous_revision_id"], "content.previous_revision_id"
            ),
        )
    except (TypeError, ValueError) as error:
        raise ComponentMaterialProjectError("content_assignment_invalid") from error
    if assignment.as_dict() != raw:
        raise ComponentMaterialProjectError("content_assignment_content_invalid")
    return assignment


def _deserialize_pcr_declaration(value: object) -> PCRDeclarationRevision:
    raw = _mapping(
        value,
        {
            "contract",
            "revision_id",
            "material_id",
            "recycled_content_percentage",
            "status",
            "external_authority_reference",
            "provenance",
            "authority_semantics",
            "external_reference_independently_verified_by_packlab",
            "recycled_content_certified",
            "environmental_performance_verified",
            "regulatory_approval",
            "physical_or_environmental_claim",
        },
        "pcr_declaration",
    )
    if (
        raw["authority_semantics"] != "USER_SUPPLIED_OR_DESIGN_INTENT_METADATA_ONLY"
        or raw["external_reference_independently_verified_by_packlab"] is not False
        or raw["recycled_content_certified"] is not False
        or raw["environmental_performance_verified"] is not False
        or raw["regulatory_approval"] is not False
        or raw["physical_or_environmental_claim"] is not False
    ):
        raise ComponentMaterialProjectError("pcr_declaration_authority_invalid")
    provenance = _mapping(
        raw["provenance"], {"design_model_revision_id", "component_id"}, "pcr.provenance"
    )
    external = raw["external_authority_reference"]
    try:
        authority = None
        if external is not None:
            external_raw = _mapping(
                external,
                {"authority_name", "reference_id", "document_sha256"},
                "pcr.external_authority",
            )
            authority = ExternalAuthorityReference(
                _string(external_raw["authority_name"], "pcr.authority_name"),
                _string(external_raw["reference_id"], "pcr.authority_reference_id"),
                _string(external_raw["document_sha256"], "pcr.authority_digest"),
            )
        declaration = PCRDeclarationRevision(
            revision_id=_string(raw["revision_id"], "pcr.revision_id"),
            material_id=_string(raw["material_id"], "pcr.material_id"),
            recycled_content_percentage=_number(
                raw["recycled_content_percentage"], "pcr.percentage"
            ),
            status=PCRDeclarationStatus(_string(raw["status"], "pcr.status")),
            design_model_revision_id=_string(
                provenance["design_model_revision_id"], "pcr.design_model_revision_id"
            ),
            component_id=_string(provenance["component_id"], "pcr.component_id"),
            external_authority=authority,
        )
    except (ValueError, TypeError) as error:
        if isinstance(error, ComponentMaterialProjectError):
            raise
        raise ComponentMaterialProjectError("pcr_declaration_invalid") from error
    if declaration.as_dict() != raw:
        raise ComponentMaterialProjectError("pcr_declaration_content_invalid")
    return declaration


def _deserialize_pcr_variant(value: object) -> PCRVisualVariantRevision:
    raw = _mapping(
        value,
        {
            "contract",
            "revision_id",
            "declaration_revision_id",
            "material_id",
            "variant_id",
            "display_name",
            "appearance_metadata",
            "provenance",
            "authority_semantics",
            "recycled_content_certified",
            "environmental_performance_verified",
            "regulatory_approval",
            "physical_or_environmental_claim",
        },
        "pcr_variant",
    )
    if (
        raw["authority_semantics"] != "NON_CERTIFIED_VISUAL_VARIANT"
        or raw["recycled_content_certified"] is not False
        or raw["environmental_performance_verified"] is not False
        or raw["regulatory_approval"] is not False
        or raw["physical_or_environmental_claim"] is not False
    ):
        raise ComponentMaterialProjectError("pcr_visual_variant_authority_invalid")
    appearance = _mapping(
        raw["appearance_metadata"], {"color_rgba", "coordinate_unit"}, "variant.appearance"
    )
    if appearance["coordinate_unit"] != "unitless_visual_metadata":
        raise ComponentMaterialProjectError("pcr_visual_variant_unit_invalid")
    provenance = _mapping(
        raw["provenance"], {"design_model_revision_id", "component_id"}, "variant.provenance"
    )
    color = _number_array(appearance["color_rgba"], 4, "variant.color")
    try:
        variant = PCRVisualVariantRevision(
            revision_id=_string(raw["revision_id"], "variant.revision_id"),
            declaration_revision_id=_string(
                raw["declaration_revision_id"], "variant.declaration_revision_id"
            ),
            material_id=_string(raw["material_id"], "variant.material_id"),
            variant_id=_string(raw["variant_id"], "variant.variant_id"),
            display_name=_string(raw["display_name"], "variant.display_name"),
            appearance_color_rgba=(color[0], color[1], color[2], color[3]),
            design_model_revision_id=_string(
                provenance["design_model_revision_id"], "variant.design_model_revision_id"
            ),
            component_id=_string(provenance["component_id"], "variant.component_id"),
        )
    except ValueError as error:
        raise ComponentMaterialProjectError("pcr_visual_variant_invalid") from error
    if variant.as_dict() != raw:
        raise ComponentMaterialProjectError("pcr_visual_variant_content_invalid")
    return variant


def _mapping(value: object, fields: set[str], name: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ComponentMaterialProjectError(f"{name}_fields_invalid")
    return value


def _array(value: object, name: str) -> list[object]:
    if not isinstance(value, list):
        raise ComponentMaterialProjectError(f"{name}_must_be_array")
    return value


def _string(value: object, name: str) -> str:
    if not isinstance(value, str):
        raise ComponentMaterialProjectError(f"{name}_must_be_string")
    return value


def _optional_string(value: object, name: str) -> str | None:
    return None if value is None else _string(value, name)


def _number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComponentMaterialProjectError(f"{name}_must_be_number")
    try:
        number = float(value)
    except OverflowError as error:
        raise ComponentMaterialProjectError(f"{name}_must_be_finite") from error
    if not math.isfinite(number):
        raise ComponentMaterialProjectError(f"{name}_must_be_finite")
    return number


def _optional_number(value: object, name: str) -> float | None:
    return None if value is None else _number(value, name)


def _number_array(value: object, length: int, name: str) -> list[float]:
    raw = _array(value, name)
    if len(raw) != length:
        raise ComponentMaterialProjectError(f"{name}_length_invalid")
    return [_number(item, name) for item in raw]


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ComponentMaterialProjectError("component_material_project_duplicate_key")
        result[key] = value
    return result


def _canonical_json(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ComponentMaterialProjectError(
            "component_material_project_not_canonical_json"
        ) from error


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


__all__ = [
    "COMPONENT_MATERIAL_PROJECT_CONTRACT",
    "COMPONENT_MATERIAL_PROJECT_SCHEMA_VERSION",
    "ComponentMaterialProjectDocument",
    "ComponentMaterialProjectEntry",
    "ComponentMaterialProjectError",
    "create_component_material_project",
    "deserialize_component_material_project",
    "remove_component_material_project_entry",
    "replace_component_material_project_entry",
]
