"""Immutable reusable closure components and explicitly evidenced compatibility links."""

from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from .packaging_asset import (
    DesignModelLink,
    FieldProvenance,
    PackagingAsset,
    ProvenanceClass,
)

_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_MAX_COMPATIBILITY_LINKS = 10_000


class PackagingComponentError(ValueError):
    """Raised when component metadata or compatibility evidence is invalid."""


class PackagingComponentKind(StrEnum):
    CAP = "CAP"
    TRIGGER = "TRIGGER"
    PUMP = "PUMP"


class CompatibilityClass(StrEnum):
    SUPPLIER_DECLARED = "SUPPLIER_DECLARED"
    USER_DECLARED = "USER_DECLARED"
    PACKLAB_ESTIMATE = "PACKLAB_ESTIMATE"


class CompatibilityResult(StrEnum):
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"
    UNKNOWN = "UNKNOWN"


class CompatibilityBasis(StrEnum):
    SUPPLIER_SPECIFICATION = "SUPPLIER_SPECIFICATION"
    USER_DECLARATION = "USER_DECLARATION"
    NECK_FINISH_REFERENCE = "NECK_FINISH_REFERENCE"
    VISUAL_SIMILARITY = "VISUAL_SIMILARITY"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class ReusablePackagingComponent:
    """Path-free reusable component metadata; optional geometry remains a revision link."""

    component_id: str
    kind: PackagingComponentKind
    display_name: str
    interface_reference: str | None = None
    interface_provenance: FieldProvenance | None = None
    design_model_link: DesignModelLink | None = None
    contract: str = "packlab.reusable-packaging-component.v1"

    def __post_init__(self) -> None:
        if self.contract != "packlab.reusable-packaging-component.v1":
            raise PackagingComponentError("packaging_component_contract_invalid")
        _identifier(self.component_id, "component_id")
        if not isinstance(self.kind, PackagingComponentKind):
            raise PackagingComponentError("packaging_component_kind_invalid")
        _bounded_text(self.display_name, "display_name", 120)
        if self.interface_reference is None:
            if self.interface_provenance is not None:
                if (
                    not isinstance(self.interface_provenance, FieldProvenance)
                    or self.interface_provenance.field_name != "component_interface_reference"
                    or self.interface_provenance.classification is not ProvenanceClass.UNKNOWN
                ):
                    raise PackagingComponentError("component_interface_unknown_provenance_invalid")
        else:
            _bounded_text(self.interface_reference, "interface_reference", 80)
            if (
                not isinstance(self.interface_provenance, FieldProvenance)
                or self.interface_provenance.field_name != "component_interface_reference"
                or self.interface_provenance.classification is ProvenanceClass.UNKNOWN
            ):
                raise PackagingComponentError("component_interface_provenance_required")
        if self.design_model_link is not None and not isinstance(
            self.design_model_link, DesignModelLink
        ):
            raise PackagingComponentError("component_design_model_link_invalid")

    @property
    def revision_id(self) -> str:
        return (
            "packaging-component:" + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()
        )

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "component_id": self.component_id,
            "kind": self.kind.value,
            "display_name": self.display_name,
            "interface_reference": self.interface_reference,
            "interface_provenance": (
                self.interface_provenance.as_dict()
                if self.interface_provenance is not None
                else None
            ),
            "design_model_link": (
                self.design_model_link.as_dict() if self.design_model_link is not None else None
            ),
            "geometry_stored_in_library": False,
        }


@dataclass(frozen=True, slots=True)
class CompatibilityEvidence:
    """Explicit authority/evidence for one body-to-component compatibility assertion."""

    classification: CompatibilityClass
    basis: CompatibilityBasis
    source_reference_id: str | None = None
    source_description: str | None = None
    method_id: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.classification, CompatibilityClass):
            raise PackagingComponentError("compatibility_classification_invalid")
        if not isinstance(self.basis, CompatibilityBasis):
            raise PackagingComponentError("compatibility_basis_invalid")
        if self.source_reference_id is not None:
            _identifier(self.source_reference_id, "compatibility_source_reference_id")
        if self.source_description is not None:
            _bounded_text(self.source_description, "compatibility_source_description", 160)
        if self.method_id is not None:
            _identifier(self.method_id, "compatibility_method_id")
        if self.confidence is not None:
            if isinstance(self.confidence, bool) or not isinstance(self.confidence, (int, float)):
                raise PackagingComponentError("compatibility_confidence_invalid")
            try:
                confidence = float(self.confidence)
            except OverflowError as error:
                raise PackagingComponentError("compatibility_confidence_invalid") from error
            if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
                raise PackagingComponentError("compatibility_confidence_invalid")
            object.__setattr__(self, "confidence", confidence)
        if self.classification is CompatibilityClass.SUPPLIER_DECLARED:
            if (
                self.source_reference_id is None
                and self.source_description is None
                or self.method_id is not None
                or self.confidence is not None
                or self.basis is not CompatibilityBasis.SUPPLIER_SPECIFICATION
            ):
                raise PackagingComponentError("supplier_compatibility_evidence_invalid")
        elif self.classification is CompatibilityClass.USER_DECLARED:
            if (
                self.basis is not CompatibilityBasis.USER_DECLARATION
                or self.source_reference_id is not None
                or self.method_id is not None
                or self.confidence is not None
            ):
                raise PackagingComponentError("user_compatibility_evidence_invalid")
        elif (
            self.method_id is None
            or self.source_reference_id is not None
            or self.source_description is not None
            or self.basis is CompatibilityBasis.SUPPLIER_SPECIFICATION
        ):
            raise PackagingComponentError("estimated_compatibility_evidence_invalid")

    def as_dict(self) -> dict[str, object]:
        return {
            "classification": self.classification.value,
            "basis": self.basis.value,
            "source_reference_id": self.source_reference_id,
            "source_description": self.source_description,
            "method_id": self.method_id,
            "confidence": self.confidence,
        }


@dataclass(frozen=True, slots=True)
class PackagingCompatibilityLink:
    """Immutable link between exact body/component revisions with explicit evidence."""

    body_asset_id: str
    body_revision_id: str
    component_id: str
    component_revision_id: str
    component_kind: PackagingComponentKind
    result: CompatibilityResult
    evidence: CompatibilityEvidence
    contract: str = "packlab.packaging-compatibility-link.v1"

    def __post_init__(self) -> None:
        if self.contract != "packlab.packaging-compatibility-link.v1":
            raise PackagingComponentError("compatibility_link_contract_invalid")
        _identifier(self.body_asset_id, "compatibility_body_asset_id")
        _identifier(self.body_revision_id, "compatibility_body_revision_id")
        _identifier(self.component_id, "compatibility_component_id")
        _identifier(self.component_revision_id, "compatibility_component_revision_id")
        if not isinstance(self.component_kind, PackagingComponentKind):
            raise PackagingComponentError("compatibility_component_kind_invalid")
        if not isinstance(self.result, CompatibilityResult):
            raise PackagingComponentError("compatibility_result_invalid")
        if not isinstance(self.evidence, CompatibilityEvidence):
            raise PackagingComponentError("compatibility_evidence_required")

    @property
    def revision_id(self) -> str:
        return (
            "packaging-compatibility:"
            + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()
        )

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "body": {"asset_id": self.body_asset_id, "revision_id": self.body_revision_id},
            "component": {
                "component_id": self.component_id,
                "revision_id": self.component_revision_id,
                "kind": self.component_kind.value,
            },
            "result": self.result.value,
            "evidence": self.evidence.as_dict(),
            "fit_verified": False,
            "supplier_fit_certified": False,
            "compatibility_inferred_from_visual_similarity": False,
        }

    def validate_targets(self, body: PackagingAsset, component: ReusablePackagingComponent) -> None:
        """Fail closed when either exact immutable target revision is missing or stale."""
        if (
            not isinstance(body, PackagingAsset)
            or body.asset_id != self.body_asset_id
            or body.revision_id != self.body_revision_id
        ):
            raise PackagingComponentError("compatibility_body_target_stale_or_missing")
        if (
            not isinstance(component, ReusablePackagingComponent)
            or component.component_id != self.component_id
            or component.revision_id != self.component_revision_id
            or component.kind is not self.component_kind
        ):
            raise PackagingComponentError("compatibility_component_target_stale_or_missing")


def create_compatibility_link(
    body: PackagingAsset,
    component: ReusablePackagingComponent,
    *,
    result: CompatibilityResult,
    evidence: CompatibilityEvidence,
) -> PackagingCompatibilityLink:
    """Create a reference-only compatibility revision; never infer fit from shape/name."""
    if not isinstance(body, PackagingAsset):
        raise PackagingComponentError("compatibility_body_required")
    if not isinstance(component, ReusablePackagingComponent):
        raise PackagingComponentError("compatibility_component_required")
    return PackagingCompatibilityLink(
        body.asset_id,
        body.revision_id,
        component.component_id,
        component.revision_id,
        component.kind,
        result,
        evidence,
    )


@dataclass(frozen=True, slots=True)
class PackagingCompatibilityIndex:
    """Bounded immutable many-to-many index of exact body/component link revisions."""

    links: tuple[PackagingCompatibilityLink, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.links, tuple) or any(
            not isinstance(item, PackagingCompatibilityLink) for item in self.links
        ):
            raise PackagingComponentError("compatibility_index_links_invalid")
        if len(self.links) > _MAX_COMPATIBILITY_LINKS:
            raise PackagingComponentError("compatibility_index_limit_exceeded")
        identities = tuple(
            (
                item.body_asset_id,
                item.body_revision_id,
                item.component_id,
                item.component_revision_id,
            )
            for item in self.links
        )
        if len(identities) != len(set(identities)):
            raise PackagingComponentError("compatibility_link_duplicate")
        canonical_links = tuple(
            sorted(
                self.links,
                key=lambda item: (
                    item.body_asset_id,
                    item.body_revision_id,
                    item.component_id,
                    item.component_revision_id,
                ),
            )
        )
        if canonical_links != self.links:
            object.__setattr__(self, "links", canonical_links)

    @property
    def revision_id(self) -> str:
        return (
            "packaging-compatibility-index:"
            + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()
        )

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.packaging-compatibility-index.v1",
            "links": [item.as_dict() for item in self.links],
        }

    def with_link(
        self,
        link: PackagingCompatibilityLink,
        body: PackagingAsset,
        component: ReusablePackagingComponent,
    ) -> PackagingCompatibilityIndex:
        if not isinstance(link, PackagingCompatibilityLink):
            raise PackagingComponentError("compatibility_link_required")
        link.validate_targets(body, component)
        return PackagingCompatibilityIndex((*self.links, link))


def _identifier(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PackagingComponentError(f"packaging_component_{field_name}_invalid")


def _bounded_text(value: object, field_name: str, maximum: int) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > maximum
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or re.match(
            r"^(?:[A-Za-z]:[\\/]|[\\/]{1,2}|[A-Za-z][A-Za-z0-9+.-]*://|file:)", value.strip(), re.I
        )
    ):
        raise PackagingComponentError(f"packaging_component_{field_name}_invalid")


__all__ = [
    "CompatibilityBasis",
    "CompatibilityClass",
    "CompatibilityEvidence",
    "CompatibilityResult",
    "PackagingCompatibilityLink",
    "PackagingCompatibilityIndex",
    "PackagingComponentError",
    "PackagingComponentKind",
    "ReusablePackagingComponent",
    "create_compatibility_link",
]
