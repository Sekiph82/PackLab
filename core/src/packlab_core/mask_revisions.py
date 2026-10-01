"""Immutable publication and freshness checks for mask-set revisions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from .segmentation import MaskArtifact, MaskSetRevision, SegmentationContractError


class MaskRevisionError(ValueError):
    """Raised for ambiguous, conflicting, or out-of-order mask revisions."""


class StaleMaskGeometryError(MaskRevisionError):
    """Raised when geometry is bound to a mask set other than the current one."""


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _mask_identity(mask: MaskArtifact) -> dict[str, object]:
    """Return all serialized authority fields except the non-authority timestamp."""
    return {key: value for key, value in mask.as_dict().items() if key != "created_at"}


@dataclass(frozen=True, slots=True)
class GeometryMaskRevisionBinding:
    """The mask-set dependency a downstream geometry result was derived from."""

    project_id: str
    source_revision: str
    mask_set_revision_id: str
    mask_set_revision_digest: str

    def __post_init__(self) -> None:
        for name in ("project_id", "source_revision", "mask_set_revision_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise MaskRevisionError(f"{name} must be non-empty text")
        if (
            not isinstance(self.mask_set_revision_digest, str)
            or len(self.mask_set_revision_digest) != 64
            or any(
                character not in "0123456789abcdef" for character in self.mask_set_revision_digest
            )
        ):
            raise MaskRevisionError("mask_set_revision_digest must be lowercase SHA-256")

    @classmethod
    def from_revision(cls, revision: MaskSetRevision) -> GeometryMaskRevisionBinding:
        return cls(
            revision.project_id,
            revision.source_revision,
            revision.revision_id,
            revision.revision_digest,
        )

    def require_current(self, revision: MaskSetRevision) -> None:
        if (
            self.project_id != revision.project_id
            or self.source_revision != revision.source_revision
            or self.mask_set_revision_id != revision.revision_id
            or self.mask_set_revision_digest != revision.revision_digest
        ):
            raise StaleMaskGeometryError(
                "downstream geometry is stale and must be regenerated for the current mask set"
            )

    def as_dict(self) -> dict[str, str]:
        return {
            "project_id": self.project_id,
            "source_revision": self.source_revision,
            "mask_set_revision_id": self.mask_set_revision_id,
            "mask_set_revision_digest": self.mask_set_revision_digest,
        }


class MaskRevisionService:
    """Publish deterministic immutable snapshots and retain their parent chain."""

    def __init__(self) -> None:
        self._revisions: dict[str, MaskSetRevision] = {}
        self._heads: dict[tuple[str, str], str] = {}

    def current(self, project_id: str, source_revision: str) -> MaskSetRevision | None:
        revision_id = self._heads.get((project_id, source_revision))
        return None if revision_id is None else self._revisions[revision_id]

    def history(self, project_id: str, source_revision: str) -> tuple[MaskSetRevision, ...]:
        return tuple(
            revision
            for revision in self._revisions.values()
            if revision.project_id == project_id and revision.source_revision == source_revision
        )

    def publish_initial(
        self,
        *,
        project_id: str,
        source_revision: str,
        masks: Sequence[MaskArtifact],
        created_at: str,
    ) -> MaskSetRevision:
        key = (project_id, source_revision)
        if key in self._heads:
            raise MaskRevisionError("mask-set initial revision already exists")
        return self._publish(
            project_id=project_id,
            source_revision=source_revision,
            masks=masks,
            created_at=created_at,
            parent_revision_id=None,
            parent_revision_digest=None,
        )

    def publish_child(
        self,
        parent: MaskSetRevision,
        *,
        replacements: Mapping[str, MaskArtifact] | None = None,
        additions: Sequence[MaskArtifact] = (),
        created_at: str,
    ) -> MaskSetRevision:
        key = (parent.project_id, parent.source_revision)
        if (
            self._heads.get(key) != parent.revision_id
            or self._revisions.get(parent.revision_id) != parent
        ):
            raise MaskRevisionError("parent mask-set revision is not the current head")
        replacement_map = dict(replacements or {})
        if not replacement_map and not additions:
            raise MaskRevisionError("child revision must replace or add at least one mask")
        by_id = {mask.artifact_id: mask for mask in parent.masks}
        if len(by_id) != len(parent.masks):
            raise MaskRevisionError("parent revision contains ambiguous duplicate artifact IDs")
        for prior_artifact_id, child in replacement_map.items():
            prior = by_id.get(prior_artifact_id)
            if prior is None:
                raise MaskRevisionError(
                    "replacement parent artifact does not exist in the parent set"
                )
            self._validate_replacement(prior, child)

        next_masks = [replacement_map.get(mask.artifact_id, mask) for mask in parent.masks]
        next_masks.extend(additions)
        return self._publish(
            project_id=parent.project_id,
            source_revision=parent.source_revision,
            masks=next_masks,
            created_at=created_at,
            parent_revision_id=parent.revision_id,
            parent_revision_digest=parent.revision_digest,
        )

    def bind_geometry(self, revision: MaskSetRevision) -> GeometryMaskRevisionBinding:
        known = self._revisions.get(revision.revision_id)
        if known is None or known.revision_digest != revision.revision_digest:
            raise MaskRevisionError("geometry can bind only to a published mask-set revision")
        return GeometryMaskRevisionBinding.from_revision(revision)

    def require_geometry_current(
        self, binding: GeometryMaskRevisionBinding, *, project_id: str, source_revision: str
    ) -> None:
        revision = self.current(project_id, source_revision)
        if revision is None:
            raise StaleMaskGeometryError("no current mask-set revision exists for this geometry")
        binding.require_current(revision)

    def _publish(
        self,
        *,
        project_id: str,
        source_revision: str,
        masks: Sequence[MaskArtifact],
        created_at: str,
        parent_revision_id: str | None,
        parent_revision_digest: str | None,
    ) -> MaskSetRevision:
        mask_tuple = tuple(masks)
        if not all(isinstance(mask, MaskArtifact) for mask in mask_tuple):
            raise MaskRevisionError("mask-set entries must be MaskArtifact values")
        if not mask_tuple:
            raise MaskRevisionError("mask-set revision must contain at least one mask")
        if len({mask.artifact_id for mask in mask_tuple}) != len(mask_tuple):
            raise MaskRevisionError("duplicate or ambiguous mask artifact IDs are not allowed")
        if len({mask.mask_revision for mask in mask_tuple}) != len(mask_tuple):
            raise MaskRevisionError("duplicate or ambiguous mask revision IDs are not allowed")
        ordered_masks = tuple(
            sorted(
                mask_tuple,
                key=lambda item: (item.source_image_asset_id, item.artifact_id, item.mask_revision),
            )
        )
        identity: dict[str, object] = {
            "schema": "packlab.mask-set-revision.v1",
            "project_id": project_id,
            "source_revision": source_revision,
            "parent_revision_id": parent_revision_id,
            "parent_revision_digest": parent_revision_digest,
            "masks": [_mask_identity(mask) for mask in ordered_masks],
        }
        revision_id = f"maskset:{_digest(identity)}"
        try:
            revision = MaskSetRevision(
                project_id=project_id,
                revision_id=revision_id,
                source_revision=source_revision,
                masks=ordered_masks,
                created_at=created_at,
                parent_revision_id=parent_revision_id,
            )
        except SegmentationContractError as error:
            raise MaskRevisionError(str(error)) from error

        existing = self._revisions.get(revision_id)
        if existing is not None:
            if existing.revision_digest != revision.revision_digest:
                raise MaskRevisionError(
                    "deterministic revision ID conflicts with published content"
                )
            return existing
        self._revisions[revision_id] = revision
        self._heads[(project_id, source_revision)] = revision_id
        return revision

    @staticmethod
    def _validate_replacement(parent: MaskArtifact, child: MaskArtifact) -> None:
        if child.artifact_id == parent.artifact_id:
            raise MaskRevisionError("replacement must use a new immutable mask artifact ID")
        if child.parent_mask_revision != parent.mask_revision:
            raise MaskRevisionError(
                "replacement does not declare the prior mask revision as parent"
            )
        if (
            child.manual_edit_ancestry[: len(parent.manual_edit_ancestry)]
            != parent.manual_edit_ancestry
        ):
            raise MaskRevisionError("replacement does not preserve prior manual edit ancestry")
        if child.manual_edit_evidence is None or len(child.manual_edit_ancestry) <= len(
            parent.manual_edit_ancestry
        ):
            raise MaskRevisionError("replacement must append explicit manual edit provenance")
        evidence = child.manual_edit_evidence
        if evidence.get("parent_revision") != parent.mask_revision:
            raise MaskRevisionError("manual edit evidence does not bind the parent mask revision")
        identity_digest = evidence.get("revision_identity_sha256")
        editor_id = evidence.get("editor_id")
        ancestry_entry = child.manual_edit_ancestry[-1]
        if (
            not isinstance(ancestry_entry, str)
            or not isinstance(identity_digest, str)
            or not identity_digest
            or not isinstance(editor_id, str)
            or not editor_id
            or identity_digest not in ancestry_entry
            or editor_id not in ancestry_entry
        ):
            raise MaskRevisionError("manual ancestry does not identify the appended editor action")
        if (
            child.source_image_asset_id != parent.source_image_asset_id
            or child.source_digest != parent.source_digest
            or (child.source_width, child.source_height)
            != (parent.source_width, parent.source_height)
            or child.transform != parent.transform
            or child.provenance != parent.provenance
        ):
            raise MaskRevisionError(
                "manual replacement changed immutable source or model provenance"
            )
