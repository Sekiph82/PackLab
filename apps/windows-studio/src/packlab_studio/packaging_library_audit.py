"""Atomic optimistic metadata mutations with an append-only integrity chain."""

from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from packlab_core.packaging_asset import PackagingAsset

_STATE_FILE = "packaging-library-state.json"
_LOCK_FILE = ".packaging-library-state.lock"
_STATE_REVISION_PREFIX = "packaging-library-state:"
_EVENT_ID_PREFIX = "packaging-library-event:"
_ASSET_REVISION_PREFIX = "packaging-asset:"
_RELATIONSHIP_ID_PREFIX = "packaging-relationship:"
_RELATIONSHIP_REVISION_PREFIX = "packaging-relationship-revision:"
_RELATIONSHIP_ID = re.compile(r"^packaging-relationship:[0-9a-f]{64}$")
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_.:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_MAX_EVENTS = 100_000
_MAX_CHANGED_FIELDS = 32
_RELATIONSHIP_FIELDS = frozenset(
    {
        "actor_id",
        "asset_a_id",
        "asset_b_id",
        "provenance_class",
        "reason",
        "relationship_type",
        "source_reference_id",
        "timestamp_utc",
    }
)
_SAFE_ASSET_FIELDS = frozenset(
    {
        "asset_id",
        "authority_semantics",
        "base_material",
        "contract",
        "dimensions",
        "display_name",
        "empty_package_weight",
        "family",
        "field_provenance",
        "manufacturing_authorized",
        "neck_closure",
        "nominal_volume",
        "other_family_label",
        "other_material_label",
        "physical_accuracy_verified",
        "source_links",
        "status",
        "supplier",
        "supplier_certification_inferred",
    }
)


class PackagingLibraryAuditError(ValueError):
    """Raised when a mutation is stale, invalid or fails audit replay."""


class StalePackagingLibraryState(PackagingLibraryAuditError):
    """Raised when the caller's expected state revision is no longer current."""


@dataclass(frozen=True, slots=True)
class PackagingLibraryAuditEvent:
    event_id: str
    event_digest: str
    previous_event_digest: str
    previous_state_revision: str
    state_revision: str
    actor_id: str
    timestamp_utc: str
    reason: str
    operation_type: str
    target_entity_ids: tuple[str, ...]
    before_revision_id: str | None
    after_revision_id: str
    changed_field_names: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "event_digest": self.event_digest,
            "previous_event_digest": self.previous_event_digest,
            "previous_state_revision": self.previous_state_revision,
            "state_revision": self.state_revision,
            "actor_id": self.actor_id,
            "timestamp_utc": self.timestamp_utc,
            "reason": self.reason,
            "operation_type": self.operation_type,
            "target_entity_ids": list(self.target_entity_ids),
            "before_revision_id": self.before_revision_id,
            "after_revision_id": self.after_revision_id,
            "changed_field_names": list(self.changed_field_names),
        }


@dataclass(frozen=True, slots=True)
class PackagingLibraryAssetEntry:
    asset_id: str
    revision_id: str
    canonical_json: str


@dataclass(frozen=True, slots=True)
class PackagingAssetRelationship:
    relationship_type: str
    asset_a_id: str
    asset_b_id: str
    provenance_class: str
    actor_id: str
    reason: str
    timestamp_utc: str
    source_reference_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.relationship_type, str) or self.relationship_type not in {
            "DUPLICATE",
            "VARIANT",
        }:
            raise PackagingLibraryAuditError("packaging_library_relationship_type_invalid")
        _validate_id(self.asset_a_id, "relationship_asset")
        _validate_id(self.asset_b_id, "relationship_asset")
        if self.asset_a_id == self.asset_b_id:
            raise PackagingLibraryAuditError("packaging_library_relationship_self_link_invalid")
        if self.relationship_type == "DUPLICATE" and self.asset_a_id > self.asset_b_id:
            raise PackagingLibraryAuditError("packaging_library_duplicate_order_invalid")
        if not isinstance(self.provenance_class, str) or self.provenance_class not in {
            "SUPPLIER_FACT",
            "USER_DECLARED",
            "PACKLAB_ESTIMATE",
        }:
            raise PackagingLibraryAuditError("packaging_library_relationship_provenance_invalid")
        _validate_actor(self.actor_id)
        _validate_reason(self.reason)
        _validate_timestamp(self.timestamp_utc)
        if self.source_reference_id is not None:
            _validate_id(self.source_reference_id, "relationship_source")

    @property
    def relationship_id(self) -> str:
        identity = {
            "relationship_type": self.relationship_type,
            "asset_a_id": self.asset_a_id,
            "asset_b_id": self.asset_b_id,
        }
        return (
            _RELATIONSHIP_ID_PREFIX
            + hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
        )

    @property
    def revision_id(self) -> str:
        return (
            _RELATIONSHIP_REVISION_PREFIX
            + hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()
        )

    @property
    def canonical_json(self) -> str:
        return _canonical_json(
            {
                "relationship_id": self.relationship_id,
                "relationship_type": self.relationship_type,
                "asset_a_id": self.asset_a_id,
                "asset_b_id": self.asset_b_id,
                "provenance_class": self.provenance_class,
                "source_reference_id": self.source_reference_id,
                "actor_id": self.actor_id,
                "reason": self.reason,
                "timestamp_utc": self.timestamp_utc,
            }
        )

    def as_dict(self) -> dict[str, object]:
        return {
            "relationship_id": self.relationship_id,
            "relationship_type": self.relationship_type,
            "asset_a_id": self.asset_a_id,
            "asset_b_id": self.asset_b_id,
            "provenance_class": self.provenance_class,
            "source_reference_id": self.source_reference_id,
            "actor_id": self.actor_id,
            "reason": self.reason,
            "timestamp_utc": self.timestamp_utc,
            "revision_id": self.revision_id,
        }


@dataclass(frozen=True, slots=True)
class PackagingLibraryAuditSnapshot:
    state_revision: str
    audit_head_digest: str
    assets: tuple[PackagingLibraryAssetEntry, ...]
    events: tuple[PackagingLibraryAuditEvent, ...]
    relationships: tuple[PackagingAssetRelationship, ...] = ()


class PackagingLibraryAuditStore:
    """Persist asset documents and their audit chain in one atomic state file."""

    def __init__(
        self,
        library_root: str | Path,
        *,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        if not isinstance(library_root, (str, Path)) or not str(library_root).strip():
            raise PackagingLibraryAuditError("packaging_library_root_required")
        self.root = Path(library_root).expanduser().absolute()
        if self.root.exists() and self.root.is_symlink():
            raise PackagingLibraryAuditError("packaging_library_root_symlink_forbidden")
        self.root.mkdir(parents=True, exist_ok=True)
        if self.root.is_symlink() or not self.root.is_dir():
            raise PackagingLibraryAuditError("packaging_library_root_invalid")
        self.state_path = self.root / _STATE_FILE
        self.lock_path = self.root / _LOCK_FILE
        self._thread_lock = threading.RLock()
        self._clock = clock or (lambda: datetime.now(UTC))

    def snapshot(self) -> PackagingLibraryAuditSnapshot:
        return self._load()

    def validate(self) -> PackagingLibraryAuditSnapshot:
        """Replay the full chain and confirm its head and current asset revisions."""
        return self._load()

    def create_asset(
        self,
        asset: PackagingAsset,
        *,
        expected_state_revision: str,
        actor_id: str,
        reason: str,
    ) -> PackagingLibraryAuditSnapshot:
        if not isinstance(asset, PackagingAsset):
            raise PackagingLibraryAuditError("packaging_library_asset_required")
        return self._mutate(
            asset,
            operation_type="CREATE",
            expected_state_revision=expected_state_revision,
            expected_asset_revision_id=None,
            actor_id=actor_id,
            reason=reason,
        )

    def update_asset(
        self,
        asset: PackagingAsset,
        *,
        expected_state_revision: str,
        expected_asset_revision_id: str,
        actor_id: str,
        reason: str,
    ) -> PackagingLibraryAuditSnapshot:
        if not isinstance(asset, PackagingAsset):
            raise PackagingLibraryAuditError("packaging_library_asset_required")
        return self._mutate(
            asset,
            operation_type="UPDATE",
            expected_state_revision=expected_state_revision,
            expected_asset_revision_id=expected_asset_revision_id,
            actor_id=actor_id,
            reason=reason,
        )

    def link_source(
        self,
        asset: PackagingAsset,
        *,
        expected_state_revision: str,
        expected_asset_revision_id: str,
        actor_id: str,
        reason: str,
    ) -> PackagingLibraryAuditSnapshot:
        if not isinstance(asset, PackagingAsset):
            raise PackagingLibraryAuditError("packaging_library_asset_required")
        return self._mutate(
            asset,
            operation_type="LINK",
            expected_state_revision=expected_state_revision,
            expected_asset_revision_id=expected_asset_revision_id,
            actor_id=actor_id,
            reason=reason,
        )

    def unlink_source(
        self,
        asset: PackagingAsset,
        *,
        expected_state_revision: str,
        expected_asset_revision_id: str,
        actor_id: str,
        reason: str,
    ) -> PackagingLibraryAuditSnapshot:
        if not isinstance(asset, PackagingAsset):
            raise PackagingLibraryAuditError("packaging_library_asset_required")
        return self._mutate(
            asset,
            operation_type="UNLINK",
            expected_state_revision=expected_state_revision,
            expected_asset_revision_id=expected_asset_revision_id,
            actor_id=actor_id,
            reason=reason,
        )

    def create_relationship(
        self,
        relationship_type: str,
        asset_a_id: str,
        asset_b_id: str,
        *,
        expected_state_revision: str,
        expected_asset_revisions: tuple[tuple[str, str], ...],
        actor_id: str,
        reason: str,
        provenance_class: str = "USER_DECLARED",
        source_reference_id: str | None = None,
    ) -> PackagingLibraryAuditSnapshot:
        """Create an explicit duplicate or directed parent-to-variant relationship."""
        _validate_id(asset_a_id, "relationship_asset")
        _validate_id(asset_b_id, "relationship_asset")
        if not isinstance(relationship_type, str) or relationship_type not in {
            "DUPLICATE",
            "VARIANT",
        }:
            raise PackagingLibraryAuditError("packaging_library_relationship_type_invalid")
        if relationship_type == "DUPLICATE" and asset_b_id < asset_a_id:
            asset_a_id, asset_b_id = asset_b_id, asset_a_id
        _validate_actor(actor_id)
        _validate_reason(reason)
        _validate_revision(expected_state_revision, _STATE_REVISION_PREFIX, "expected_state")
        if asset_a_id == asset_b_id:
            raise PackagingLibraryAuditError("packaging_library_relationship_self_link_invalid")
        if not isinstance(expected_asset_revisions, tuple):
            raise PackagingLibraryAuditError(
                "packaging_library_relationship_expected_assets_invalid"
            )
        expected = dict(expected_asset_revisions)
        if len(expected) != len(expected_asset_revisions) or set(expected) != {
            asset_a_id,
            asset_b_id,
        }:
            raise PackagingLibraryAuditError(
                "packaging_library_relationship_expected_assets_invalid"
            )
        for revision in expected.values():
            _validate_revision(revision, _ASSET_REVISION_PREFIX, "expected_asset")
        with self._exclusive_lock():
            current = self._load()
            if expected_state_revision != current.state_revision:
                raise StalePackagingLibraryState("packaging_library_state_revision_stale")
            assets = {item.asset_id: item for item in current.assets}
            for asset_id in (asset_a_id, asset_b_id):
                entry = assets.get(asset_id)
                if entry is None:
                    raise PackagingLibraryAuditError("packaging_library_relationship_asset_missing")
                if expected[asset_id] != entry.revision_id:
                    raise StalePackagingLibraryState(
                        "packaging_library_relationship_asset_revision_stale"
                    )
            timestamp = _timestamp(self._clock())
            relationship = PackagingAssetRelationship(
                relationship_type=relationship_type,
                asset_a_id=asset_a_id,
                asset_b_id=asset_b_id,
                provenance_class=provenance_class,
                source_reference_id=source_reference_id,
                actor_id=actor_id,
                reason=reason,
                timestamp_utc=timestamp,
            )
            if any(
                item.relationship_id == relationship.relationship_id
                for item in current.relationships
            ):
                raise PackagingLibraryAuditError("packaging_library_relationship_already_exists")
            if relationship_type == "VARIANT" and _would_create_variant_cycle(
                current.relationships, asset_a_id, asset_b_id
            ):
                raise PackagingLibraryAuditError("packaging_library_variant_cycle_invalid")
            previous_relationship_event = next(
                (
                    event
                    for event in reversed(current.events)
                    if event.operation_type in {"RELATE", "UNRELATE"}
                    and event.target_entity_ids[0] == relationship.relationship_id
                ),
                None,
            )
            before_revision_id = (
                previous_relationship_event.after_revision_id
                if previous_relationship_event is not None
                else None
            )
            event = _new_event(
                current,
                actor_id=actor_id,
                timestamp_utc=timestamp,
                reason=reason,
                operation_type="RELATE",
                target_entity_ids=(relationship.relationship_id, asset_a_id, asset_b_id),
                before_revision_id=before_revision_id,
                after_revision_id=relationship.revision_id,
                changed_field_names=tuple(sorted(_RELATIONSHIP_FIELDS)),
            )
            updated = PackagingLibraryAuditSnapshot(
                state_revision=event.state_revision,
                audit_head_digest=event.event_digest,
                assets=current.assets,
                events=(*current.events, event),
                relationships=tuple(
                    sorted(
                        (*current.relationships, relationship),
                        key=lambda item: item.relationship_id,
                    )
                ),
            )
            self._publish(updated)
            return updated

    def remove_relationship(
        self,
        relationship_id: str,
        *,
        expected_state_revision: str,
        expected_relationship_revision_id: str,
        actor_id: str,
        reason: str,
    ) -> PackagingLibraryAuditSnapshot:
        _validate_id(relationship_id, "relationship")
        _validate_revision(expected_state_revision, _STATE_REVISION_PREFIX, "expected_state")
        _validate_revision(
            expected_relationship_revision_id,
            _RELATIONSHIP_REVISION_PREFIX,
            "expected_relationship",
        )
        _validate_actor(actor_id)
        _validate_reason(reason)
        with self._exclusive_lock():
            current = self._load()
            if expected_state_revision != current.state_revision:
                raise StalePackagingLibraryState("packaging_library_state_revision_stale")
            relationship = next(
                (item for item in current.relationships if item.relationship_id == relationship_id),
                None,
            )
            if relationship is None:
                raise PackagingLibraryAuditError("packaging_library_relationship_missing")
            if relationship.revision_id != expected_relationship_revision_id:
                raise StalePackagingLibraryState("packaging_library_relationship_revision_stale")
            timestamp = _timestamp(self._clock())
            tombstone_revision_id = (
                _RELATIONSHIP_REVISION_PREFIX
                + hashlib.sha256(
                    _canonical_json(
                        {
                            "relationship_id": relationship_id,
                            "prior_revision_id": relationship.revision_id,
                            "actor_id": actor_id,
                            "reason": reason,
                            "timestamp_utc": timestamp,
                            "active": False,
                        }
                    ).encode("utf-8")
                ).hexdigest()
            )
            event = _new_event(
                current,
                actor_id=actor_id,
                timestamp_utc=timestamp,
                reason=reason,
                operation_type="UNRELATE",
                target_entity_ids=(
                    relationship_id,
                    relationship.asset_a_id,
                    relationship.asset_b_id,
                ),
                before_revision_id=relationship.revision_id,
                after_revision_id=tombstone_revision_id,
                changed_field_names=("active",),
            )
            updated = PackagingLibraryAuditSnapshot(
                state_revision=event.state_revision,
                audit_head_digest=event.event_digest,
                assets=current.assets,
                events=(*current.events, event),
                relationships=tuple(
                    item
                    for item in current.relationships
                    if item.relationship_id != relationship_id
                ),
            )
            self._publish(updated)
            return updated

    def _mutate(
        self,
        asset: PackagingAsset,
        *,
        operation_type: str,
        expected_state_revision: str,
        expected_asset_revision_id: str | None,
        actor_id: str,
        reason: str,
    ) -> PackagingLibraryAuditSnapshot:
        _validate_actor(actor_id)
        _validate_reason(reason)
        _validate_revision(expected_state_revision, _STATE_REVISION_PREFIX, "expected_state")
        if expected_asset_revision_id is not None:
            _validate_revision(expected_asset_revision_id, _ASSET_REVISION_PREFIX, "expected_asset")

        with self._exclusive_lock():
            current = self._load()
            if expected_state_revision != current.state_revision:
                raise StalePackagingLibraryState("packaging_library_state_revision_stale")
            entries = {item.asset_id: item for item in current.assets}
            previous = entries.get(asset.asset_id)
            if operation_type == "CREATE":
                if previous is not None or expected_asset_revision_id is not None:
                    raise PackagingLibraryAuditError("packaging_library_asset_already_exists")
                before_revision_id = None
                changed_fields = tuple(sorted(asset.as_dict()))
            else:
                if previous is None:
                    raise PackagingLibraryAuditError("packaging_library_asset_missing")
                if previous.revision_id != expected_asset_revision_id:
                    raise StalePackagingLibraryState("packaging_library_asset_revision_stale")
                before_revision_id = previous.revision_id
                previous_document = json.loads(previous.canonical_json)
                next_document = asset.as_dict()
                changed_fields = tuple(
                    sorted(
                        key
                        for key in previous_document
                        if previous_document.get(key) != next_document.get(key)
                    )
                )
                if not changed_fields:
                    raise PackagingLibraryAuditError("packaging_library_noop_mutation")
                if any(key not in _SAFE_ASSET_FIELDS for key in changed_fields):
                    raise PackagingLibraryAuditError("packaging_library_changed_field_forbidden")
                if operation_type == "UPDATE" and "source_links" in changed_fields:
                    raise PackagingLibraryAuditError("packaging_library_link_operation_required")
                if operation_type in {"LINK", "UNLINK"}:
                    if changed_fields != ("source_links",) or not _valid_link_delta(
                        previous_document["source_links"],
                        next_document["source_links"],
                        operation_type,
                    ):
                        raise PackagingLibraryAuditError("packaging_library_link_delta_invalid")

            target_entity_ids = _target_ids(asset, previous, operation_type)
            if operation_type == "CREATE":
                target_entity_ids = (asset.asset_id,)
            event = _new_event(
                current,
                actor_id=actor_id,
                timestamp_utc=_timestamp(self._clock()),
                reason=reason,
                operation_type=operation_type,
                target_entity_ids=target_entity_ids,
                before_revision_id=before_revision_id,
                after_revision_id=asset.revision_id,
                changed_field_names=changed_fields,
            )
            entries[asset.asset_id] = PackagingLibraryAssetEntry(
                asset.asset_id, asset.revision_id, asset.canonical_json
            )
            updated = PackagingLibraryAuditSnapshot(
                state_revision=event.state_revision,
                audit_head_digest=event.event_digest,
                assets=tuple(sorted(entries.values(), key=lambda item: item.asset_id)),
                events=(*current.events, event),
            )
            self._publish(updated)
            return updated

    def _load(self) -> PackagingLibraryAuditSnapshot:
        if not self.state_path.exists():
            if self.state_path.is_symlink():
                raise PackagingLibraryAuditError("packaging_library_state_symlink_forbidden")
            return PackagingLibraryAuditSnapshot(_genesis_state_revision(), "", (), ())
        if self.state_path.is_symlink() or not self.state_path.is_file():
            raise PackagingLibraryAuditError("packaging_library_state_file_unsafe")
        try:
            value = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(value, dict) or value.get("schema_version") not in {1, 2}:
                raise PackagingLibraryAuditError("packaging_library_state_schema_invalid")
            raw_assets = value.get("assets")
            raw_events = value.get("events")
            raw_relationships = value.get("relationships", [])
            if (
                not isinstance(raw_assets, list)
                or not isinstance(raw_events, list)
                or not isinstance(raw_relationships, list)
            ):
                raise PackagingLibraryAuditError("packaging_library_state_shape_invalid")
            if len(raw_events) > _MAX_EVENTS:
                raise PackagingLibraryAuditError("packaging_library_event_limit_exceeded")
            assets = tuple(_parse_asset_entry(item) for item in raw_assets)
            events = tuple(_parse_event(item) for item in raw_events)
            relationships = tuple(_parse_relationship(item) for item in raw_relationships)
            if len({item.asset_id for item in assets}) != len(assets):
                raise PackagingLibraryAuditError("packaging_library_asset_duplicate")
            if len({item.relationship_id for item in relationships}) != len(relationships):
                raise PackagingLibraryAuditError("packaging_library_relationship_duplicate")
            snapshot = PackagingLibraryAuditSnapshot(
                state_revision=value["state_revision"],
                audit_head_digest=value["audit_head_digest"],
                assets=tuple(sorted(assets, key=lambda item: item.asset_id)),
                events=events,
                relationships=tuple(sorted(relationships, key=lambda item: item.relationship_id)),
            )
            _validate_snapshot(snapshot)
            return snapshot
        except PackagingLibraryAuditError:
            raise
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
            raise PackagingLibraryAuditError("packaging_library_state_corrupt") from error

    def _publish(self, snapshot: PackagingLibraryAuditSnapshot) -> None:
        _validate_snapshot(snapshot)
        value = {
            "schema_version": 2,
            "state_revision": snapshot.state_revision,
            "audit_head_digest": snapshot.audit_head_digest,
            "assets": [
                {
                    "asset_id": item.asset_id,
                    "revision_id": item.revision_id,
                    "document": json.loads(item.canonical_json),
                }
                for item in snapshot.assets
            ],
            "events": [item.as_dict() for item in snapshot.events],
            "relationships": [item.as_dict() for item in snapshot.relationships],
        }
        _atomic_json(self.state_path, value)

    @contextmanager
    def _exclusive_lock(self) -> Iterator[None]:
        with self._thread_lock:
            if self.lock_path.is_symlink():
                raise PackagingLibraryAuditError("packaging_library_lock_symlink_forbidden")
            descriptor = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
            try:
                if os.name == "nt":
                    import msvcrt

                    if os.fstat(descriptor).st_size == 0:
                        os.write(descriptor, b"0")
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
                    try:
                        yield
                    finally:
                        os.lseek(descriptor, 0, os.SEEK_SET)
                        msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
                else:
                    import fcntl

                    file_lock = getattr(fcntl, "flock")
                    lock_exclusive = getattr(fcntl, "LOCK_EX")
                    lock_release = getattr(fcntl, "LOCK_UN")
                    file_lock(descriptor, lock_exclusive)
                    try:
                        yield
                    finally:
                        file_lock(descriptor, lock_release)
            finally:
                os.close(descriptor)


def _new_event(
    previous: PackagingLibraryAuditSnapshot,
    *,
    actor_id: str,
    timestamp_utc: str,
    reason: str,
    operation_type: str,
    target_entity_ids: tuple[str, ...],
    before_revision_id: str | None,
    after_revision_id: str,
    changed_field_names: tuple[str, ...],
) -> PackagingLibraryAuditEvent:
    base: dict[str, object] = {
        "previous_event_digest": previous.audit_head_digest,
        "previous_state_revision": previous.state_revision,
        "actor_id": actor_id,
        "timestamp_utc": timestamp_utc,
        "reason": reason,
        "operation_type": operation_type,
        "target_entity_ids": list(target_entity_ids),
        "before_revision_id": before_revision_id,
        "after_revision_id": after_revision_id,
        "changed_field_names": list(changed_field_names),
    }
    state_revision = (
        _STATE_REVISION_PREFIX + hashlib.sha256(_canonical_json(base).encode("utf-8")).hexdigest()
    )
    digest_payload = {**base, "state_revision": state_revision}
    event_digest = hashlib.sha256(_canonical_json(digest_payload).encode("utf-8")).hexdigest()
    return PackagingLibraryAuditEvent(
        event_id=_EVENT_ID_PREFIX + event_digest,
        event_digest=event_digest,
        previous_event_digest=previous.audit_head_digest,
        previous_state_revision=previous.state_revision,
        state_revision=state_revision,
        actor_id=actor_id,
        timestamp_utc=timestamp_utc,
        reason=reason,
        operation_type=operation_type,
        target_entity_ids=target_entity_ids,
        before_revision_id=before_revision_id,
        after_revision_id=after_revision_id,
        changed_field_names=changed_field_names,
    )


def _parse_event(value: object) -> PackagingLibraryAuditEvent:
    if not isinstance(value, dict):
        raise PackagingLibraryAuditError("packaging_library_event_invalid")
    try:
        event = PackagingLibraryAuditEvent(
            event_id=value["event_id"],
            event_digest=value["event_digest"],
            previous_event_digest=value["previous_event_digest"],
            previous_state_revision=value["previous_state_revision"],
            state_revision=value["state_revision"],
            actor_id=value["actor_id"],
            timestamp_utc=value["timestamp_utc"],
            reason=value["reason"],
            operation_type=value["operation_type"],
            target_entity_ids=tuple(value["target_entity_ids"]),
            before_revision_id=value["before_revision_id"],
            after_revision_id=value["after_revision_id"],
            changed_field_names=tuple(value["changed_field_names"]),
        )
    except (KeyError, TypeError) as error:
        raise PackagingLibraryAuditError("packaging_library_event_invalid") from error
    _validate_event_shape(event)
    return event


def _parse_asset_entry(value: object) -> PackagingLibraryAssetEntry:
    if not isinstance(value, dict) or not isinstance(value.get("document"), dict):
        raise PackagingLibraryAuditError("packaging_library_asset_entry_invalid")
    document = value["document"]
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    asset_id = value.get("asset_id")
    revision_id = value.get("revision_id")
    _validate_id(asset_id, "asset")
    expected = _ASSET_REVISION_PREFIX + hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if (
        document.get("asset_id") != asset_id
        or revision_id != expected
        or document.get("contract") != "packlab.packaging-asset.v1"
    ):
        raise PackagingLibraryAuditError("packaging_library_asset_revision_invalid")
    return PackagingLibraryAssetEntry(asset_id, revision_id, canonical)


def _parse_relationship(value: object) -> PackagingAssetRelationship:
    if not isinstance(value, dict):
        raise PackagingLibraryAuditError("packaging_library_relationship_invalid")
    try:
        relationship = PackagingAssetRelationship(
            relationship_type=value["relationship_type"],
            asset_a_id=value["asset_a_id"],
            asset_b_id=value["asset_b_id"],
            provenance_class=value["provenance_class"],
            source_reference_id=value["source_reference_id"],
            actor_id=value["actor_id"],
            reason=value["reason"],
            timestamp_utc=value["timestamp_utc"],
        )
    except (KeyError, TypeError) as error:
        raise PackagingLibraryAuditError("packaging_library_relationship_invalid") from error
    if (
        value.get("relationship_id") != relationship.relationship_id
        or value.get("revision_id") != relationship.revision_id
    ):
        raise PackagingLibraryAuditError("packaging_library_relationship_revision_invalid")
    return relationship


def _validate_snapshot(snapshot: PackagingLibraryAuditSnapshot) -> None:
    state_revision = _genesis_state_revision()
    event_digest = ""
    seen_event_ids: set[str] = set()
    replayed_assets: dict[str, str] = {}
    replayed_relationships: dict[str, tuple[str, bool, tuple[str, ...]]] = {}
    for event in snapshot.events:
        _validate_event_shape(event)
        if event.event_id in seen_event_ids:
            raise PackagingLibraryAuditError("packaging_library_event_id_duplicate")
        seen_event_ids.add(event.event_id)
        if (
            event.previous_event_digest != event_digest
            or event.previous_state_revision != state_revision
        ):
            raise PackagingLibraryAuditError("packaging_library_audit_chain_disconnected")
        expected = _new_event(
            PackagingLibraryAuditSnapshot(state_revision, event_digest, (), ()),
            actor_id=event.actor_id,
            timestamp_utc=event.timestamp_utc,
            reason=event.reason,
            operation_type=event.operation_type,
            target_entity_ids=event.target_entity_ids,
            before_revision_id=event.before_revision_id,
            after_revision_id=event.after_revision_id,
            changed_field_names=event.changed_field_names,
        )
        if (event.state_revision, event.event_digest, event.event_id) != (
            expected.state_revision,
            expected.event_digest,
            expected.event_id,
        ):
            raise PackagingLibraryAuditError("packaging_library_event_digest_invalid")
        if event.operation_type in {"RELATE", "UNRELATE"}:
            relationship_id = event.target_entity_ids[0]
            current = replayed_relationships.get(relationship_id)
            if any(asset_id not in replayed_assets for asset_id in event.target_entity_ids[1:]):
                raise PackagingLibraryAuditError(
                    "packaging_library_relationship_event_asset_missing"
                )
            if event.operation_type == "RELATE":
                expected_before = current[0] if current is not None else None
                if (
                    current is not None and current[1]
                ) or event.before_revision_id != expected_before:
                    raise PackagingLibraryAuditError(
                        "packaging_library_relationship_event_before_revision_invalid"
                    )
                replayed_relationships[relationship_id] = (
                    event.after_revision_id,
                    True,
                    event.target_entity_ids,
                )
            else:
                if (
                    current is None
                    or not current[1]
                    or current[0] != event.before_revision_id
                    or current[2] != event.target_entity_ids
                ):
                    raise PackagingLibraryAuditError(
                        "packaging_library_relationship_event_remove_invalid"
                    )
                replayed_relationships[relationship_id] = (
                    event.after_revision_id,
                    False,
                    event.target_entity_ids,
                )
        else:
            asset_id = event.target_entity_ids[0]
            current_revision = replayed_assets.get(asset_id)
            if event.operation_type == "CREATE":
                if current_revision is not None or event.before_revision_id is not None:
                    raise PackagingLibraryAuditError("packaging_library_event_create_invalid")
            elif current_revision != event.before_revision_id:
                raise PackagingLibraryAuditError("packaging_library_event_before_revision_invalid")
            replayed_assets[asset_id] = event.after_revision_id
        event_digest = event.event_digest
        state_revision = event.state_revision
    current_assets = {item.asset_id: item.revision_id for item in snapshot.assets}
    if current_assets != replayed_assets:
        raise PackagingLibraryAuditError("packaging_library_audit_state_mismatch")
    current_relationships = {item.relationship_id: item for item in snapshot.relationships}
    replayed_active = {
        relationship_id: (revision_id, targets)
        for relationship_id, (revision_id, active, targets) in replayed_relationships.items()
        if active
    }
    if set(current_relationships) != set(replayed_active):
        raise PackagingLibraryAuditError("packaging_library_relationship_state_mismatch")
    asset_ids = set(current_assets)
    for relationship_id, relationship in current_relationships.items():
        replayed_revision, targets = replayed_active[relationship_id]
        if (
            relationship.revision_id != replayed_revision
            or targets != (relationship_id, relationship.asset_a_id, relationship.asset_b_id)
            or relationship.asset_a_id not in asset_ids
            or relationship.asset_b_id not in asset_ids
        ):
            raise PackagingLibraryAuditError("packaging_library_relationship_state_mismatch")
    if _has_variant_cycle(snapshot.relationships):
        raise PackagingLibraryAuditError("packaging_library_variant_cycle_invalid")
    if (snapshot.state_revision, snapshot.audit_head_digest) != (state_revision, event_digest):
        raise PackagingLibraryAuditError("packaging_library_audit_head_mismatch")


def _validate_event_shape(event: PackagingLibraryAuditEvent) -> None:
    _validate_id(event.event_id, "event")
    if not isinstance(event.event_digest, str) or not _SHA256.fullmatch(event.event_digest):
        raise PackagingLibraryAuditError("packaging_library_event_digest_invalid")
    if event.event_id != _EVENT_ID_PREFIX + event.event_digest:
        raise PackagingLibraryAuditError("packaging_library_event_id_invalid")
    if event.previous_event_digest and not _SHA256.fullmatch(event.previous_event_digest):
        raise PackagingLibraryAuditError("packaging_library_previous_digest_invalid")
    _validate_revision(event.previous_state_revision, _STATE_REVISION_PREFIX, "previous_state")
    _validate_revision(event.state_revision, _STATE_REVISION_PREFIX, "state")
    _validate_actor(event.actor_id)
    _validate_timestamp(event.timestamp_utc)
    _validate_reason(event.reason)
    if event.operation_type not in {
        "CREATE",
        "UPDATE",
        "LINK",
        "UNLINK",
        "RELATE",
        "UNRELATE",
    }:
        raise PackagingLibraryAuditError("packaging_library_operation_type_invalid")
    if (
        not isinstance(event.target_entity_ids, tuple)
        or not 1 <= len(event.target_entity_ids) <= 8
        or len(set(event.target_entity_ids)) != len(event.target_entity_ids)
    ):
        raise PackagingLibraryAuditError("packaging_library_event_targets_invalid")
    for target in event.target_entity_ids:
        _validate_id(target, "target")
    relationship_event = event.operation_type in {"RELATE", "UNRELATE"}
    if relationship_event:
        if (
            len(event.target_entity_ids) != 3
            or not _RELATIONSHIP_ID.fullmatch(event.target_entity_ids[0])
            or event.target_entity_ids[1] == event.target_entity_ids[2]
        ):
            raise PackagingLibraryAuditError("packaging_library_relationship_event_targets_invalid")
        revision_prefix = _RELATIONSHIP_REVISION_PREFIX
        allowed_fields = _RELATIONSHIP_FIELDS | {"active"}
    else:
        revision_prefix = _ASSET_REVISION_PREFIX
        allowed_fields = _SAFE_ASSET_FIELDS
    if event.before_revision_id is not None:
        _validate_revision(event.before_revision_id, revision_prefix, "before_entity")
    _validate_revision(event.after_revision_id, revision_prefix, "after_entity")
    if (
        not isinstance(event.changed_field_names, tuple)
        or not 1 <= len(event.changed_field_names) <= _MAX_CHANGED_FIELDS
        or len(set(event.changed_field_names)) != len(event.changed_field_names)
        or tuple(sorted(event.changed_field_names)) != event.changed_field_names
        or any(name not in allowed_fields for name in event.changed_field_names)
    ):
        raise PackagingLibraryAuditError("packaging_library_changed_fields_invalid")
    if relationship_event:
        if event.operation_type == "RELATE" and event.changed_field_names != tuple(
            sorted(_RELATIONSHIP_FIELDS)
        ):
            raise PackagingLibraryAuditError("packaging_library_relationship_create_fields_invalid")
        if event.operation_type == "UNRELATE" and (
            event.changed_field_names != ("active",) or event.before_revision_id is None
        ):
            raise PackagingLibraryAuditError("packaging_library_relationship_remove_fields_invalid")
        if event.before_revision_id == event.after_revision_id:
            raise PackagingLibraryAuditError("packaging_library_noop_event_invalid")
        return
    if event.operation_type == "CREATE" and event.before_revision_id is not None:
        raise PackagingLibraryAuditError("packaging_library_event_create_invalid")
    if event.operation_type != "CREATE" and event.before_revision_id is None:
        raise PackagingLibraryAuditError("packaging_library_event_before_revision_required")
    if event.operation_type == "CREATE" and event.changed_field_names != tuple(
        sorted(_SAFE_ASSET_FIELDS)
    ):
        raise PackagingLibraryAuditError("packaging_library_create_fields_invalid")
    if event.operation_type != "CREATE" and event.before_revision_id == event.after_revision_id:
        raise PackagingLibraryAuditError("packaging_library_noop_event_invalid")
    if event.operation_type in {"LINK", "UNLINK"} and event.changed_field_names != (
        "source_links",
    ):
        raise PackagingLibraryAuditError("packaging_library_link_event_fields_invalid")
    if event.operation_type == "UPDATE" and "source_links" in event.changed_field_names:
        raise PackagingLibraryAuditError("packaging_library_link_event_required")


def _valid_link_delta(before: object, after: object, operation_type: str) -> bool:
    if not isinstance(before, dict) or not isinstance(after, dict):
        return False
    changed = False
    for key in ("raw_scans", "design_models"):
        old_values, new_values = before.get(key), after.get(key)
        if not isinstance(old_values, list) or not isinstance(new_values, list):
            return False
        old_set = {_canonical_json(item) for item in old_values}
        new_set = {_canonical_json(item) for item in new_values}
        if operation_type == "LINK" and not old_set <= new_set:
            return False
        if operation_type == "UNLINK" and not new_set <= old_set:
            return False
        changed = changed or old_set != new_set
    old_scan, new_scan = before.get("scan_master"), after.get("scan_master")
    if operation_type == "LINK":
        if old_scan is not None and (new_scan is None or old_scan != new_scan):
            return False
        if old_scan is None and new_scan is not None:
            changed = True
        return changed
    if new_scan is not None and old_scan != new_scan:
        return False
    if old_scan is not None and new_scan is None:
        changed = True
    return changed


def _would_create_variant_cycle(
    relationships: tuple[PackagingAssetRelationship, ...],
    parent_asset_id: str,
    variant_asset_id: str,
) -> bool:
    edges: dict[str, set[str]] = {}
    for relationship in relationships:
        if relationship.relationship_type == "VARIANT":
            edges.setdefault(relationship.asset_a_id, set()).add(relationship.asset_b_id)
    pending = [variant_asset_id]
    visited: set[str] = set()
    while pending:
        current = pending.pop()
        if current == parent_asset_id:
            return True
        if current in visited:
            continue
        visited.add(current)
        pending.extend(edges.get(current, ()))
    return False


def _has_variant_cycle(relationships: tuple[PackagingAssetRelationship, ...]) -> bool:
    edges: dict[str, set[str]] = {}
    for relationship in relationships:
        if relationship.relationship_type == "VARIANT":
            edges.setdefault(relationship.asset_a_id, set()).add(relationship.asset_b_id)
    state: dict[str, int] = {}
    for root in edges:
        if state.get(root) == 2:
            continue
        pending: list[tuple[str, bool]] = [(root, False)]
        while pending:
            asset_id, exiting = pending.pop()
            if exiting:
                state[asset_id] = 2
                continue
            status = state.get(asset_id, 0)
            if status == 1:
                return True
            if status == 2:
                continue
            state[asset_id] = 1
            pending.append((asset_id, True))
            for child in edges.get(asset_id, ()):
                if state.get(child) == 1:
                    return True
                if state.get(child, 0) == 0:
                    pending.append((child, False))
    return False


def _target_ids(
    asset: PackagingAsset,
    previous: PackagingLibraryAssetEntry | None,
    operation_type: str,
) -> tuple[str, ...]:
    if previous is None or operation_type not in {"LINK", "UNLINK"}:
        return (asset.asset_id,)
    old_links = json.loads(previous.canonical_json)["source_links"]
    new_links = asset.as_dict()["source_links"]
    changed: set[str] = {asset.asset_id}
    for links in (old_links, new_links):
        for key in ("raw_scans", "design_models"):
            for link in links.get(key, []):
                if isinstance(link, dict):
                    changed.update(
                        value
                        for name in ("project_id", "revision_id")
                        if isinstance((value := link.get(name)), str)
                    )
        scan_master = links.get("scan_master")
        if isinstance(scan_master, dict):
            changed.update(
                value
                for name in ("project_id", "revision_id")
                if isinstance((value := scan_master.get(name)), str)
            )
    return (asset.asset_id, *sorted(changed - {asset.asset_id}))


def _validate_actor(actor_id: str) -> None:
    _validate_id(actor_id, "actor")


def _validate_id(value: object, field_name: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise PackagingLibraryAuditError(f"packaging_library_{field_name}_id_invalid")


def _validate_revision(value: object, prefix: str, field_name: str) -> None:
    if (
        not isinstance(value, str)
        or not value.startswith(prefix)
        or not _SHA256.fullmatch(value[len(prefix) :])
    ):
        raise PackagingLibraryAuditError(f"packaging_library_{field_name}_revision_invalid")


def _validate_timestamp(value: object) -> None:
    if not isinstance(value, str):
        raise PackagingLibraryAuditError("packaging_library_timestamp_invalid")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as error:
        raise PackagingLibraryAuditError("packaging_library_timestamp_invalid") from error
    if parsed.tzinfo is not None:
        raise PackagingLibraryAuditError("packaging_library_timestamp_invalid")


def _timestamp(value: datetime) -> str:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() != UTC.utcoffset(value)
    ):
        raise PackagingLibraryAuditError("packaging_library_clock_must_be_utc")
    return value.astimezone(UTC).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _validate_reason(value: str) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
        or len(value) > 240
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
        or "/" in value
        or "\\" in value
        or re.match(r"^[A-Za-z]:", value)
        or re.search(r"(?:password|secret|token|private[_ ]key|api[_ ]key)\s*[:=]", value, re.I)
    ):
        raise PackagingLibraryAuditError("packaging_library_reason_invalid_or_sensitive")


def _genesis_state_revision() -> str:
    return (
        _STATE_REVISION_PREFIX + hashlib.sha256(b"packlab.packaging-library-state.v1").hexdigest()
    )


def _canonical_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )


def _atomic_json(target: Path, value: object) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{target.name}-", suffix=".tmp", dir=target.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(
                value,
                handle,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            )
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


__all__ = [
    "PackagingLibraryAssetEntry",
    "PackagingLibraryAuditError",
    "PackagingLibraryAuditEvent",
    "PackagingLibraryAuditSnapshot",
    "PackagingLibraryAuditStore",
    "StalePackagingLibraryState",
]
