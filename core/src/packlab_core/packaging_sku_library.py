"""Portable SKU records that reference geometry and artwork revisions without copying them."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum

from .label_artwork import (
    LabelArtworkAssetRevision,
    LabelArtworkAssignmentRevision,
    LabelArtworkMappingRevision,
)
from .label_zone import LabelZone
from .packaging_asset import DesignModelLink, PackagingAsset

_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_MAX_SKU_REVISIONS = 100_000


class PackagingSkuError(ValueError):
    """Raised when a Packaging SKU or its immutable references are invalid."""


class PackagingSkuStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


@dataclass(frozen=True, slots=True)
class SkuArtworkPresentationReference:
    """Exact Label Zone/artwork/mapping/assignment IDs; never embeds artwork bytes."""

    label_zone_id: str
    label_zone_design_model_revision_id: str
    label_zone_brep_revision_id: str
    label_zone_brep_geometry_sha256: str
    artwork_revision_id: str | None = None
    artwork_content_sha256: str | None = None
    mapping_revision_id: str | None = None
    assignment_revision_id: str | None = None
    variant_id: str | None = None

    def __post_init__(self) -> None:
        _identifier(self.label_zone_id, "label_zone_id")
        _identifier(self.label_zone_design_model_revision_id, "label_zone_design_model_revision_id")
        _identifier(self.label_zone_brep_revision_id, "label_zone_brep_revision_id")
        if not re.fullmatch(r"[0-9a-f]{64}", self.label_zone_brep_geometry_sha256):
            raise PackagingSkuError("sku_label_zone_brep_digest_invalid")
        for name in (
            "artwork_revision_id",
            "mapping_revision_id",
            "assignment_revision_id",
        ):
            value = getattr(self, name)
            if value is not None:
                _identifier(value, name)
        if self.artwork_content_sha256 is not None and not re.fullmatch(
            r"[0-9a-f]{64}", self.artwork_content_sha256
        ):
            raise PackagingSkuError("sku_artwork_digest_invalid")
        if self.mapping_revision_id is not None and self.artwork_revision_id is None:
            raise PackagingSkuError("sku_mapping_without_artwork")
        if any(
            value is None
            for value in (
                self.artwork_revision_id,
                self.artwork_content_sha256,
                self.mapping_revision_id,
                self.assignment_revision_id,
                self.variant_id,
            )
        ):
            raise PackagingSkuError("sku_artwork_presentation_reference_incomplete")
        if self.assignment_revision_id is not None and (
            self.mapping_revision_id is None
            or self.artwork_revision_id is None
            or self.variant_id is None
        ):
            raise PackagingSkuError("sku_assignment_reference_incomplete")
        if self.assignment_revision_id is None and self.variant_id is not None:
            raise PackagingSkuError("sku_variant_without_assignment")
        if self.variant_id is not None:
            _identifier(self.variant_id, "variant_id")

    @classmethod
    def from_accepted_assignment(
        cls,
        zone: LabelZone,
        artwork: LabelArtworkAssetRevision,
        mapping: LabelArtworkMappingRevision,
        assignment: LabelArtworkAssignmentRevision,
    ) -> SkuArtworkPresentationReference:
        """Build from matching immutable M14 revisions and reject stale/mixed inputs."""
        if not isinstance(zone, LabelZone):
            raise PackagingSkuError("sku_label_zone_required")
        if not isinstance(artwork, LabelArtworkAssetRevision):
            raise PackagingSkuError("sku_artwork_revision_required")
        if not isinstance(mapping, LabelArtworkMappingRevision):
            raise PackagingSkuError("sku_artwork_mapping_required")
        if not isinstance(assignment, LabelArtworkAssignmentRevision):
            raise PackagingSkuError("sku_artwork_assignment_required")
        if (
            assignment.status != "ASSIGNED"
            or assignment.zone_id != zone.zone_id
            or assignment.artwork_revision_id != artwork.revision_id
            or assignment.mapping_revision_id != mapping.revision_id
            or assignment.placement_revision_id != mapping.placement_revision_id
            or assignment.zone_kind != zone.zone_kind.value
            or mapping.zone_id != zone.zone_id
            or mapping.source_artwork_revision_id != artwork.revision_id
            or mapping.source_artwork_sha256 != artwork.content_sha256
        ):
            raise PackagingSkuError("sku_artwork_assignment_stale_or_mismatched")
        return cls(
            label_zone_id=zone.zone_id,
            label_zone_design_model_revision_id=zone.source_design_model_revision_id,
            label_zone_brep_revision_id=zone.source_brep_revision_id,
            label_zone_brep_geometry_sha256=zone.source_brep_geometry_sha256,
            artwork_revision_id=artwork.revision_id,
            artwork_content_sha256=artwork.content_sha256,
            mapping_revision_id=mapping.revision_id,
            assignment_revision_id=assignment.revision_id,
            variant_id=assignment.variant_id,
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "label_zone_id": self.label_zone_id,
            "label_zone_design_model_revision_id": self.label_zone_design_model_revision_id,
            "label_zone_brep": {
                "revision_id": self.label_zone_brep_revision_id,
                "geometry_sha256": self.label_zone_brep_geometry_sha256,
            },
            "artwork_revision_id": self.artwork_revision_id,
            "artwork_content_sha256": self.artwork_content_sha256,
            "mapping_revision_id": self.mapping_revision_id,
            "assignment_revision_id": self.assignment_revision_id,
            "variant_id": self.variant_id,
            "artwork_bytes_included": False,
            "artwork_authority_mutated": False,
        }


@dataclass(frozen=True, slots=True)
class PackagingSkuRevision:
    """One immutable POVU SKU revision pinned to an exact Packaging Asset revision."""

    sku_id: str
    display_name: str
    status: PackagingSkuStatus
    packaging_asset_id: str
    packaging_asset_revision_id: str
    preferred_design_model_link: DesignModelLink | None = None
    artwork_references: tuple[SkuArtworkPresentationReference, ...] = ()
    contract: str = "packlab.packaging-sku.v1"

    def __post_init__(self) -> None:
        if self.contract != "packlab.packaging-sku.v1":
            raise PackagingSkuError("packaging_sku_contract_invalid")
        _identifier(self.sku_id, "sku_id")
        _bounded_text(self.display_name, "display_name", 120)
        if not isinstance(self.status, PackagingSkuStatus):
            raise PackagingSkuError("packaging_sku_status_invalid")
        _identifier(self.packaging_asset_id, "packaging_asset_id")
        _identifier(self.packaging_asset_revision_id, "packaging_asset_revision_id")
        if self.preferred_design_model_link is not None and not isinstance(
            self.preferred_design_model_link, DesignModelLink
        ):
            raise PackagingSkuError("packaging_sku_design_model_link_invalid")
        if not isinstance(self.artwork_references, tuple) or any(
            not isinstance(item, SkuArtworkPresentationReference)
            for item in self.artwork_references
        ):
            raise PackagingSkuError("packaging_sku_artwork_references_invalid")
        identities = tuple(
            (
                item.label_zone_id,
                item.label_zone_design_model_revision_id,
                item.label_zone_brep_revision_id,
                item.artwork_revision_id,
                item.mapping_revision_id,
                item.assignment_revision_id,
            )
            for item in self.artwork_references
        )
        if len(identities) != len(set(identities)):
            raise PackagingSkuError("packaging_sku_artwork_reference_duplicate")
        canonical_artwork = tuple(
            sorted(
                self.artwork_references,
                key=lambda item: (
                    item.label_zone_id,
                    item.assignment_revision_id or "",
                    item.artwork_revision_id or "",
                    item.mapping_revision_id or "",
                ),
            )
        )
        if canonical_artwork != self.artwork_references:
            object.__setattr__(self, "artwork_references", canonical_artwork)

    @classmethod
    def create(
        cls,
        asset: PackagingAsset,
        *,
        sku_id: str,
        display_name: str,
        status: PackagingSkuStatus,
        preferred_design_model_link: DesignModelLink | None = None,
        artwork_references: tuple[SkuArtworkPresentationReference, ...] = (),
    ) -> PackagingSkuRevision:
        if not isinstance(asset, PackagingAsset):
            raise PackagingSkuError("packaging_sku_asset_required")
        revision = cls(
            sku_id=sku_id,
            display_name=display_name,
            status=status,
            packaging_asset_id=asset.asset_id,
            packaging_asset_revision_id=asset.revision_id,
            preferred_design_model_link=preferred_design_model_link,
            artwork_references=artwork_references,
        )
        revision.validate_targets((asset,), artwork_references)
        return revision

    @property
    def revision_id(self) -> str:
        return "packaging-sku:" + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": self.contract,
            "sku_id": self.sku_id,
            "display_name": self.display_name,
            "status": self.status.value,
            "geometry_reference": {
                "packaging_asset_id": self.packaging_asset_id,
                "revision_id": self.packaging_asset_revision_id,
                "geometry_copied": False,
                "source_mutated": False,
            },
            "preferred_design_model": (
                self.preferred_design_model_link.as_dict()
                if self.preferred_design_model_link is not None
                else None
            ),
            "artwork_presentations": [item.as_dict() for item in self.artwork_references],
            "artwork_bytes_included": False,
        }

    def validate_targets(
        self,
        assets: tuple[PackagingAsset, ...],
        artwork_references: tuple[SkuArtworkPresentationReference, ...],
    ) -> None:
        """Check exact retained source revisions; fail when any referenced target is absent."""
        if not isinstance(assets, tuple) or any(
            not isinstance(item, PackagingAsset) for item in assets
        ):
            raise PackagingSkuError("packaging_sku_asset_registry_invalid")
        matching_assets = tuple(
            item
            for item in assets
            if item.asset_id == self.packaging_asset_id
            and item.revision_id == self.packaging_asset_revision_id
        )
        if len(matching_assets) != 1:
            raise PackagingSkuError("packaging_sku_asset_target_stale_or_missing")
        asset = matching_assets[0]
        if self.preferred_design_model_link is not None and (
            self.preferred_design_model_link not in asset.design_model_links
        ):
            raise PackagingSkuError("packaging_sku_design_model_target_stale_or_missing")
        if not isinstance(artwork_references, tuple) or any(
            not isinstance(item, SkuArtworkPresentationReference) for item in artwork_references
        ):
            raise PackagingSkuError("packaging_sku_artwork_registry_invalid")
        available = set(artwork_references)
        if any(item not in available for item in self.artwork_references):
            raise PackagingSkuError("packaging_sku_artwork_target_stale_or_missing")


@dataclass(frozen=True, slots=True)
class PackagingSkuCatalog:
    """Bounded immutable history and current-revision lookup for SKU records."""

    revisions: tuple[PackagingSkuRevision, ...] = ()
    current_revision_ids: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.revisions, tuple) or any(
            not isinstance(item, PackagingSkuRevision) for item in self.revisions
        ):
            raise PackagingSkuError("packaging_sku_catalog_revisions_invalid")
        if len(self.revisions) > _MAX_SKU_REVISIONS:
            raise PackagingSkuError("packaging_sku_catalog_limit_exceeded")
        revisions_by_id = {item.revision_id: item for item in self.revisions}
        if len(revisions_by_id) != len(self.revisions):
            raise PackagingSkuError("packaging_sku_revision_duplicate")
        if not isinstance(self.current_revision_ids, tuple) or any(
            not isinstance(item, tuple)
            or len(item) != 2
            or not all(isinstance(part, str) for part in item)
            for item in self.current_revision_ids
        ):
            raise PackagingSkuError("packaging_sku_current_index_invalid")
        current_sku_ids = tuple(item[0] for item in self.current_revision_ids)
        if len(current_sku_ids) != len(set(current_sku_ids)):
            raise PackagingSkuError("packaging_sku_current_id_duplicate")
        for sku_id, revision_id in self.current_revision_ids:
            revision = revisions_by_id.get(revision_id)
            if revision is None or revision.sku_id != sku_id:
                raise PackagingSkuError("packaging_sku_current_revision_missing")
        canonical_revisions = tuple(sorted(self.revisions, key=lambda item: item.revision_id))
        if canonical_revisions != self.revisions:
            object.__setattr__(self, "revisions", canonical_revisions)
        canonical_current = tuple(sorted(self.current_revision_ids))
        if canonical_current != self.current_revision_ids:
            object.__setattr__(self, "current_revision_ids", canonical_current)

    @property
    def revision_id(self) -> str:
        return (
            "packaging-sku-catalog:"
            + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()
        )

    @property
    def canonical_json(self) -> str:
        return json.dumps(self.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False)

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.packaging-sku-catalog.v1",
            "sku_revisions": [item.as_dict() for item in self.revisions],
            "current_revision_ids": [list(item) for item in self.current_revision_ids],
        }

    def with_revision(
        self,
        sku: PackagingSkuRevision,
        *,
        assets: tuple[PackagingAsset, ...],
        artwork_references: tuple[SkuArtworkPresentationReference, ...],
    ) -> PackagingSkuCatalog:
        if not isinstance(sku, PackagingSkuRevision):
            raise PackagingSkuError("packaging_sku_revision_required")
        sku.validate_targets(assets, artwork_references)
        if any(item.revision_id == sku.revision_id for item in self.revisions):
            raise PackagingSkuError("packaging_sku_revision_duplicate")
        prior_same_sku = tuple(item for item in self.revisions if item.sku_id == sku.sku_id)
        if prior_same_sku and any(
            item.packaging_asset_id != sku.packaging_asset_id for item in prior_same_sku
        ):
            raise PackagingSkuError("packaging_sku_geometry_identity_change_forbidden")
        current = dict(self.current_revision_ids)
        current[sku.sku_id] = sku.revision_id
        return PackagingSkuCatalog(
            tuple(sorted((*self.revisions, sku), key=lambda item: item.revision_id)),
            tuple(sorted(current.items())),
        )

    def skus_for_geometry(
        self, asset_id: str, *, include_history: bool = False
    ) -> tuple[PackagingSkuRevision, ...]:
        _identifier(asset_id, "packaging_asset_id")
        if include_history:
            return tuple(item for item in self.revisions if item.packaging_asset_id == asset_id)
        revisions_by_id = {item.revision_id: item for item in self.revisions}
        return tuple(
            revisions_by_id[revision_id]
            for _, revision_id in self.current_revision_ids
            if revisions_by_id[revision_id].packaging_asset_id == asset_id
            and revisions_by_id[revision_id].status is PackagingSkuStatus.ACTIVE
        )


def _identifier(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PackagingSkuError(f"packaging_sku_{field_name}_invalid")


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
        raise PackagingSkuError(f"packaging_sku_{field_name}_invalid")


__all__ = [
    "PackagingSkuCatalog",
    "PackagingSkuError",
    "PackagingSkuRevision",
    "PackagingSkuStatus",
    "SkuArtworkPresentationReference",
]
