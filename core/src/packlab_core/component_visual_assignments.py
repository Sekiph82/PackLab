"""Separate, immutable component geometry-material and content-appearance channels."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass

from .design_model import DesignModelRevision
from .visual_material_library import (
    MaterialSourceClass,
    VisualMaterialLibraryRevision,
    VisualMaterialRecord,
)

GEOMETRY_MATERIAL_ASSIGNMENT_CONTRACT = "packlab.geometry-material-assignment.v1"
CONTENT_APPEARANCE_ASSIGNMENT_CONTRACT = "packlab.content-appearance-assignment.v1"
COMPONENT_VISUAL_STATE_CONTRACT = "packlab.component-visual-assignment-state.v1"
_IDENTIFIER = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,255}$")


class ComponentVisualAssignmentError(ValueError):
    """Raised when an immutable component visual assignment is invalid or stale."""


@dataclass(frozen=True, slots=True)
class GeometryMaterialAssignmentRevision:
    revision_id: str
    source_design_model_revision_id: str
    component_id: str
    material_library_revision_id: str | None
    material_id: str | None
    status: str
    previous_revision_id: str | None
    contract: str = GEOMETRY_MATERIAL_ASSIGNMENT_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != GEOMETRY_MATERIAL_ASSIGNMENT_CONTRACT
            or not _valid_id(self.source_design_model_revision_id)
            or not _valid_id(self.component_id)
            or not isinstance(self.status, str)
            or self.status not in {"ASSIGNED", "REMOVED"}
            or (self.previous_revision_id is not None and not _valid_id(self.previous_revision_id))
            or (
                self.status == "ASSIGNED"
                and (
                    not _valid_id(self.material_library_revision_id)
                    or not _valid_id(self.material_id)
                )
            )
            or (
                self.status == "REMOVED"
                and (self.material_library_revision_id is not None or self.material_id is not None)
            )
            or self.revision_id
            != "geometry-material-assignment:" + _digest(_geometry_assignment_identity(self))
        ):
            raise ComponentVisualAssignmentError("geometry_material_assignment_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "VISUAL_GEOMETRY_MATERIAL_ASSIGNMENT",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "component_id": self.component_id,
            "material_library_revision_id": self.material_library_revision_id,
            "material_id": self.material_id,
            "status": self.status,
            "previous_revision_id": self.previous_revision_id,
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "mutates_design_model": False,
            "physical_or_regulatory_claim": False,
        }


@dataclass(frozen=True, slots=True)
class ContentAppearanceAssignmentRevision:
    revision_id: str
    source_design_model_revision_id: str
    component_id: str
    display_name: str | None
    display_color_rgba: tuple[float, float, float, float] | None
    opacity_factor: float | None
    source_classification: MaterialSourceClass | None
    status: str
    previous_revision_id: str | None
    contract: str = CONTENT_APPEARANCE_ASSIGNMENT_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != CONTENT_APPEARANCE_ASSIGNMENT_CONTRACT
            or not _valid_id(self.source_design_model_revision_id)
            or not _valid_id(self.component_id)
            or not isinstance(self.status, str)
            or self.status not in {"ASSIGNED", "REMOVED"}
            or (self.previous_revision_id is not None and not _valid_id(self.previous_revision_id))
        ):
            raise ComponentVisualAssignmentError("content_appearance_assignment_invalid")
        if self.status == "ASSIGNED":
            _bounded_text(self.display_name, "content_display_name", 80)
            if not isinstance(self.display_color_rgba, tuple) or len(self.display_color_rgba) != 4:
                raise ComponentVisualAssignmentError("content_display_color_invalid")
            object.__setattr__(
                self,
                "display_color_rgba",
                tuple(
                    _unit_interval(channel, "content_display_color")
                    for channel in self.display_color_rgba
                ),
            )
            object.__setattr__(
                self, "opacity_factor", _unit_interval(self.opacity_factor, "content_opacity")
            )
            if not isinstance(self.source_classification, MaterialSourceClass):
                raise ComponentVisualAssignmentError("content_source_classification_invalid")
        elif any(
            value is not None
            for value in (
                self.display_name,
                self.display_color_rgba,
                self.opacity_factor,
                self.source_classification,
            )
        ):
            raise ComponentVisualAssignmentError("removed_content_appearance_must_be_empty")
        if self.revision_id != "content-appearance-assignment:" + _digest(
            _content_assignment_identity(self)
        ):
            raise ComponentVisualAssignmentError("content_appearance_assignment_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "VISUAL_PRODUCT_CONTENT_APPEARANCE_ASSIGNMENT",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "component_id": self.component_id,
            "display_name": self.display_name,
            "display_color_rgba": (
                list(self.display_color_rgba) if self.display_color_rgba is not None else None
            ),
            "opacity_factor": self.opacity_factor,
            "source_classification": (
                self.source_classification.value if self.source_classification is not None else None
            ),
            "status": self.status,
            "previous_revision_id": self.previous_revision_id,
            "authority_semantics": "NON_CERTIFIED_VISUAL_REFERENCE",
            "fill_volume_inferred": False,
            "formulation_inferred": False,
            "physical_or_regulatory_claim": False,
            "mutates_design_model": False,
        }


@dataclass(frozen=True, slots=True)
class ComponentVisualAssignmentState:
    revision_id: str
    source_design_model_revision_id: str
    component_id: str
    geometry_material_assignment: GeometryMaterialAssignmentRevision | None
    content_appearance_assignment: ContentAppearanceAssignmentRevision | None
    contract: str = COMPONENT_VISUAL_STATE_CONTRACT

    def __post_init__(self) -> None:
        if (
            self.contract != COMPONENT_VISUAL_STATE_CONTRACT
            or not _valid_id(self.source_design_model_revision_id)
            or not _valid_id(self.component_id)
            or (
                self.geometry_material_assignment is None
                and self.content_appearance_assignment is None
            )
        ):
            raise ComponentVisualAssignmentError("component_visual_state_invalid")
        for assignment in (
            self.geometry_material_assignment,
            self.content_appearance_assignment,
        ):
            if assignment is not None and (
                assignment.status != "ASSIGNED"
                or assignment.source_design_model_revision_id
                != self.source_design_model_revision_id
                or assignment.component_id != self.component_id
            ):
                raise ComponentVisualAssignmentError("component_visual_state_assignment_mismatch")
        if self.revision_id != "component-visual-state:" + _digest(_state_identity(self)):
            raise ComponentVisualAssignmentError("component_visual_state_identity_mismatch")

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "authority_class": "SEPARATE_COMPONENT_VISUAL_CHANNELS",
            "revision_id": self.revision_id,
            "source_design_model_revision_id": self.source_design_model_revision_id,
            "component_id": self.component_id,
            "geometry_material_assignment": (
                self.geometry_material_assignment.as_dict()
                if self.geometry_material_assignment is not None
                else None
            ),
            "content_appearance_assignment": (
                self.content_appearance_assignment.as_dict()
                if self.content_appearance_assignment is not None
                else None
            ),
            "geometry_and_content_channels_independent": True,
            "fill_volume_inferred": False,
            "formulation_inferred": False,
            "mutates_design_model": False,
        }


def create_geometry_material_assignment(
    model: DesignModelRevision,
    component_id: str,
    library: VisualMaterialLibraryRevision,
    material_id: str,
    *,
    previous: GeometryMaterialAssignmentRevision | None = None,
) -> GeometryMaterialAssignmentRevision:
    _validate_model_component(model, component_id)
    if not isinstance(library, VisualMaterialLibraryRevision):
        raise ComponentVisualAssignmentError("visual_material_library_required")
    material = next((item for item in library.materials if item.material_id == material_id), None)
    if not isinstance(material, VisualMaterialRecord):
        raise ComponentVisualAssignmentError("visual_material_id_not_in_library")
    previous_id = _check_previous(previous, model.revision_id, component_id, "geometry")
    values: dict[str, object] = {
        "contract": GEOMETRY_MATERIAL_ASSIGNMENT_CONTRACT,
        "source_design_model_revision_id": model.revision_id,
        "component_id": component_id,
        "material_library_revision_id": library.revision_id,
        "material_id": material.material_id,
        "status": "ASSIGNED",
        "previous_revision_id": previous_id,
    }
    return GeometryMaterialAssignmentRevision(
        revision_id="geometry-material-assignment:" + _digest(values),
        source_design_model_revision_id=model.revision_id,
        component_id=component_id,
        material_library_revision_id=library.revision_id,
        material_id=material.material_id,
        status="ASSIGNED",
        previous_revision_id=previous_id,
    )


def remove_geometry_material_assignment(
    previous: GeometryMaterialAssignmentRevision,
) -> GeometryMaterialAssignmentRevision:
    if (
        not isinstance(previous, GeometryMaterialAssignmentRevision)
        or previous.status != "ASSIGNED"
    ):
        raise ComponentVisualAssignmentError("active_geometry_material_assignment_required")
    values: dict[str, object] = {
        "contract": GEOMETRY_MATERIAL_ASSIGNMENT_CONTRACT,
        "source_design_model_revision_id": previous.source_design_model_revision_id,
        "component_id": previous.component_id,
        "material_library_revision_id": None,
        "material_id": None,
        "status": "REMOVED",
        "previous_revision_id": previous.revision_id,
    }
    return GeometryMaterialAssignmentRevision(
        revision_id="geometry-material-assignment:" + _digest(values),
        source_design_model_revision_id=previous.source_design_model_revision_id,
        component_id=previous.component_id,
        material_library_revision_id=None,
        material_id=None,
        status="REMOVED",
        previous_revision_id=previous.revision_id,
    )


def create_content_appearance_assignment(
    model: DesignModelRevision,
    component_id: str,
    *,
    display_name: str,
    display_color_rgba: tuple[float, float, float, float],
    opacity_factor: float,
    source_classification: MaterialSourceClass = MaterialSourceClass.USER_AUTHORED_VISUAL,
    previous: ContentAppearanceAssignmentRevision | None = None,
) -> ContentAppearanceAssignmentRevision:
    _validate_model_component(model, component_id)
    if not isinstance(source_classification, MaterialSourceClass):
        raise ComponentVisualAssignmentError("content_source_classification_invalid")
    previous_id = _check_previous(previous, model.revision_id, component_id, "content")
    _bounded_text(display_name, "content_display_name", 80)
    if not isinstance(display_color_rgba, tuple) or len(display_color_rgba) != 4:
        raise ComponentVisualAssignmentError("content_display_color_invalid")
    display_color: tuple[float, float, float, float] = (
        _unit_interval(display_color_rgba[0], "content_display_color"),
        _unit_interval(display_color_rgba[1], "content_display_color"),
        _unit_interval(display_color_rgba[2], "content_display_color"),
        _unit_interval(display_color_rgba[3], "content_display_color"),
    )
    opacity = _unit_interval(opacity_factor, "content_opacity")
    values: dict[str, object] = {
        "contract": CONTENT_APPEARANCE_ASSIGNMENT_CONTRACT,
        "source_design_model_revision_id": model.revision_id,
        "component_id": component_id,
        "display_name": display_name,
        "display_color_rgba": list(display_color),
        "opacity_factor": opacity,
        "source_classification": source_classification.value,
        "status": "ASSIGNED",
        "previous_revision_id": previous_id,
    }
    return ContentAppearanceAssignmentRevision(
        revision_id="content-appearance-assignment:" + _digest(values),
        source_design_model_revision_id=model.revision_id,
        component_id=component_id,
        display_name=display_name,
        display_color_rgba=display_color,
        opacity_factor=opacity,
        source_classification=source_classification,
        status="ASSIGNED",
        previous_revision_id=previous_id,
    )


def remove_content_appearance_assignment(
    previous: ContentAppearanceAssignmentRevision,
) -> ContentAppearanceAssignmentRevision:
    if (
        not isinstance(previous, ContentAppearanceAssignmentRevision)
        or previous.status != "ASSIGNED"
    ):
        raise ComponentVisualAssignmentError("active_content_appearance_assignment_required")
    values: dict[str, object] = {
        "contract": CONTENT_APPEARANCE_ASSIGNMENT_CONTRACT,
        "source_design_model_revision_id": previous.source_design_model_revision_id,
        "component_id": previous.component_id,
        "display_name": None,
        "display_color_rgba": None,
        "opacity_factor": None,
        "source_classification": None,
        "status": "REMOVED",
        "previous_revision_id": previous.revision_id,
    }
    return ContentAppearanceAssignmentRevision(
        revision_id="content-appearance-assignment:" + _digest(values),
        source_design_model_revision_id=previous.source_design_model_revision_id,
        component_id=previous.component_id,
        display_name=None,
        display_color_rgba=None,
        opacity_factor=None,
        source_classification=None,
        status="REMOVED",
        previous_revision_id=previous.revision_id,
    )


def create_component_visual_assignment_state(
    geometry_material_assignment: GeometryMaterialAssignmentRevision | None = None,
    content_appearance_assignment: ContentAppearanceAssignmentRevision | None = None,
) -> ComponentVisualAssignmentState:
    if geometry_material_assignment is not None and not isinstance(
        geometry_material_assignment, GeometryMaterialAssignmentRevision
    ):
        raise ComponentVisualAssignmentError("geometry_material_assignment_invalid")
    if content_appearance_assignment is not None and not isinstance(
        content_appearance_assignment, ContentAppearanceAssignmentRevision
    ):
        raise ComponentVisualAssignmentError("content_appearance_assignment_invalid")
    assignments = tuple(
        item
        for item in (geometry_material_assignment, content_appearance_assignment)
        if item is not None
    )
    if not assignments:
        raise ComponentVisualAssignmentError("component_visual_state_requires_assignment")
    first = assignments[0]
    model_id, component_id = (
        first.source_design_model_revision_id,
        first.component_id,
    )
    values: dict[str, object] = {
        "contract": COMPONENT_VISUAL_STATE_CONTRACT,
        "source_design_model_revision_id": model_id,
        "component_id": component_id,
        "geometry_material_assignment_revision_id": (
            geometry_material_assignment.revision_id
            if geometry_material_assignment is not None
            else None
        ),
        "content_appearance_assignment_revision_id": (
            content_appearance_assignment.revision_id
            if content_appearance_assignment is not None
            else None
        ),
    }
    return ComponentVisualAssignmentState(
        revision_id="component-visual-state:" + _digest(values),
        source_design_model_revision_id=model_id,
        component_id=component_id,
        geometry_material_assignment=geometry_material_assignment,
        content_appearance_assignment=content_appearance_assignment,
    )


def _validate_model_component(model: DesignModelRevision, component_id: str) -> None:
    if not isinstance(model, DesignModelRevision):
        raise ComponentVisualAssignmentError("design_model_revision_required")
    if not _valid_id(component_id):
        raise ComponentVisualAssignmentError("component_id_invalid")
    if not any(feature.component_id == component_id for feature in model.features):
        raise ComponentVisualAssignmentError("component_id_not_in_design_model")


def _check_previous(
    previous: GeometryMaterialAssignmentRevision | ContentAppearanceAssignmentRevision | None,
    model_revision_id: str,
    component_id: str,
    channel: str,
) -> str | None:
    if previous is None:
        return None
    expected = (
        GeometryMaterialAssignmentRevision
        if channel == "geometry"
        else ContentAppearanceAssignmentRevision
    )
    if (
        not isinstance(previous, expected)
        or previous.status != "ASSIGNED"
        or previous.source_design_model_revision_id != model_revision_id
        or previous.component_id != component_id
    ):
        raise ComponentVisualAssignmentError(f"previous_{channel}_assignment_mismatch")
    return previous.revision_id


def _geometry_assignment_identity(
    assignment: GeometryMaterialAssignmentRevision,
) -> dict[str, object]:
    return {
        "contract": assignment.contract,
        "source_design_model_revision_id": assignment.source_design_model_revision_id,
        "component_id": assignment.component_id,
        "material_library_revision_id": assignment.material_library_revision_id,
        "material_id": assignment.material_id,
        "status": assignment.status,
        "previous_revision_id": assignment.previous_revision_id,
    }


def _content_assignment_identity(
    assignment: ContentAppearanceAssignmentRevision,
) -> dict[str, object]:
    return {
        "contract": assignment.contract,
        "source_design_model_revision_id": assignment.source_design_model_revision_id,
        "component_id": assignment.component_id,
        "display_name": assignment.display_name,
        "display_color_rgba": (
            list(assignment.display_color_rgba)
            if assignment.display_color_rgba is not None
            else None
        ),
        "opacity_factor": assignment.opacity_factor,
        "source_classification": (
            assignment.source_classification.value
            if assignment.source_classification is not None
            else None
        ),
        "status": assignment.status,
        "previous_revision_id": assignment.previous_revision_id,
    }


def _state_identity(state: ComponentVisualAssignmentState) -> dict[str, object]:
    return {
        "contract": state.contract,
        "source_design_model_revision_id": state.source_design_model_revision_id,
        "component_id": state.component_id,
        "geometry_material_assignment_revision_id": (
            state.geometry_material_assignment.revision_id
            if state.geometry_material_assignment is not None
            else None
        ),
        "content_appearance_assignment_revision_id": (
            state.content_appearance_assignment.revision_id
            if state.content_appearance_assignment is not None
            else None
        ),
    }


def _bounded_text(value: object, name: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or 127 <= ord(character) <= 159 for character in value)
    ):
        raise ComponentVisualAssignmentError(f"{name}_invalid")


def _unit_interval(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComponentVisualAssignmentError(f"{name}_invalid")
    try:
        result = float(value)
    except OverflowError as error:
        raise ComponentVisualAssignmentError(f"{name}_invalid") from error
    if not math.isfinite(result) or not 0.0 <= result <= 1.0:
        raise ComponentVisualAssignmentError(f"{name}_invalid")
    return 0.0 if result == 0.0 else result


def _valid_id(value: object) -> bool:
    return isinstance(value, str) and _IDENTIFIER.fullmatch(value) is not None


def _digest(value: dict[str, object]) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    ).hexdigest()


__all__ = [
    "COMPONENT_VISUAL_STATE_CONTRACT",
    "CONTENT_APPEARANCE_ASSIGNMENT_CONTRACT",
    "GEOMETRY_MATERIAL_ASSIGNMENT_CONTRACT",
    "ComponentVisualAssignmentError",
    "ComponentVisualAssignmentState",
    "ContentAppearanceAssignmentRevision",
    "GeometryMaterialAssignmentRevision",
    "create_component_visual_assignment_state",
    "create_content_appearance_assignment",
    "create_geometry_material_assignment",
    "remove_content_appearance_assignment",
    "remove_geometry_material_assignment",
]
