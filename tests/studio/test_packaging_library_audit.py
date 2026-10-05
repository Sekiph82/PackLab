from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
from tests.core.test_packaging_asset import _asset

from packlab_core.packaging_asset import (
    FieldProvenance,
    ProvenanceClass,
    RawScanLink,
)
from packlab_studio import packaging_library_audit as audit
from packlab_studio.packaging_library_audit import (
    PackagingAssetRelationship,
    PackagingLibraryAuditError,
    PackagingLibraryAuditStore,
    StalePackagingLibraryState,
)

NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


def _store(root: Path) -> PackagingLibraryAuditStore:
    return PackagingLibraryAuditStore(root, clock=lambda: NOW)


def _created(store: PackagingLibraryAuditStore):
    initial = store.snapshot()
    created = store.create_asset(
        _asset(),
        expected_state_revision=initial.state_revision,
        actor_id="operator-1",
        reason="Record the supplier package metadata",
    )
    return initial, created


def _relationship_assets(store: PackagingLibraryAuditStore) -> dict[str, str]:
    for asset_id in ("asset-a", "asset-b", "asset-c"):
        current = store.snapshot()
        store.create_asset(
            _asset(asset_id=asset_id, display_name=f"Package {asset_id}"),
            expected_state_revision=current.state_revision,
            actor_id="operator-1",
            reason="Add separate package asset metadata",
        )
    return {entry.asset_id: entry.revision_id for entry in store.snapshot().assets}


def test_create_update_and_replay_bind_exact_asset_revisions(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    initial, created = _created(store)
    before = created.assets[0]
    updated_asset = _asset().with_field_update(
        "display_name",
        "500 mL Water Bottle Revised",
        FieldProvenance(
            "display_name",
            ProvenanceClass.PACKLAB_ESTIMATE,
            method_id="name-normalization-v1",
        ),
    )
    updated = store.update_asset(
        updated_asset,
        expected_state_revision=created.state_revision,
        expected_asset_revision_id=before.revision_id,
        actor_id="operator-1",
        reason="Correct the displayed package name",
    )

    assert initial.state_revision != created.state_revision
    assert len(updated.events) == 2
    create_event, update_event = updated.events
    assert create_event.operation_type == "CREATE"
    assert create_event.before_revision_id is None
    assert create_event.after_revision_id == before.revision_id
    assert update_event.operation_type == "UPDATE"
    assert update_event.before_revision_id == before.revision_id
    assert update_event.after_revision_id == updated_asset.revision_id
    assert update_event.changed_field_names == ("display_name", "field_provenance")
    assert update_event.previous_event_digest == create_event.event_digest
    assert updated.assets[0].canonical_json == updated_asset.canonical_json
    assert store.validate() == updated
    event_json = json.dumps([item.as_dict() for item in updated.events], sort_keys=True)
    assert "Example Supplier" not in event_json
    assert "500 mL Water Bottle Revised" not in event_json
    assert str(tmp_path) not in event_json


def test_link_and_unlink_each_append_one_exact_source_event(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    _, created = _created(store)
    original = _asset()
    linked_asset = original.with_source_links(
        raw_scan_links=(RawScanLink("project-1", "raw-rev-1", "a" * 64),),
        scan_master_link=None,
        design_model_links=(),
    )
    linked = store.link_source(
        linked_asset,
        expected_state_revision=created.state_revision,
        expected_asset_revision_id=original.revision_id,
        actor_id="operator-1",
        reason="Link the source capture revision",
    )
    removed_asset = linked_asset.with_source_links(
        raw_scan_links=(),
        scan_master_link=None,
        design_model_links=(),
    )
    unlinked = store.unlink_source(
        removed_asset,
        expected_state_revision=linked.state_revision,
        expected_asset_revision_id=linked_asset.revision_id,
        actor_id="operator-1",
        reason="Unlink the superseded source capture",
    )

    assert tuple(item.operation_type for item in unlinked.events) == (
        "CREATE",
        "LINK",
        "UNLINK",
    )
    assert unlinked.events[1].target_entity_ids == (
        "kenya-pack-001",
        "project-1",
        "raw-rev-1",
    )
    assert unlinked.events[1].changed_field_names == ("source_links",)
    assert unlinked.events[2].before_revision_id == linked_asset.revision_id
    assert unlinked.events[2].after_revision_id == removed_asset.revision_id
    assert unlinked.assets[0].revision_id == removed_asset.revision_id
    assert store.validate() == unlinked


def test_stale_library_and_asset_writers_do_not_publish(tmp_path: Path) -> None:
    root = tmp_path / "library"
    first_writer = _store(root)
    stale_writer = _store(root)
    initial = first_writer.snapshot()
    created = first_writer.create_asset(
        _asset(),
        expected_state_revision=initial.state_revision,
        actor_id="operator-1",
        reason="Create initial package record",
    )
    before = (root / "packaging-library-state.json").read_bytes()
    with pytest.raises(StalePackagingLibraryState, match="state_revision_stale"):
        stale_writer.create_asset(
            _asset(asset_id="another-pack"),
            expected_state_revision=initial.state_revision,
            actor_id="operator-2",
            reason="Try a stale library write",
        )
    with pytest.raises(StalePackagingLibraryState, match="asset_revision_stale"):
        first_writer.update_asset(
            _asset(display_name="Updated bottle"),
            expected_state_revision=created.state_revision,
            expected_asset_revision_id="packaging-asset:" + "0" * 64,
            actor_id="operator-1",
            reason="Try a stale asset write",
        )
    assert (root / "packaging-library-state.json").read_bytes() == before
    assert len(first_writer.snapshot().events) == 1


def test_atomic_publish_failure_keeps_old_state_and_event_chain(
    tmp_path: Path, monkeypatch
) -> None:
    store = _store(tmp_path / "library")
    _, created = _created(store)
    before = store.state_path.read_bytes()
    updated_asset = _asset().with_field_update(
        "display_name",
        "Atomicity Probe",
        FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
    )

    def fail_atomic_write(*_args, **_kwargs) -> None:
        raise OSError("simulated atomic state write failure")

    monkeypatch.setattr(audit, "_atomic_json", fail_atomic_write)
    with pytest.raises(OSError, match="simulated atomic state write failure"):
        store.update_asset(
            updated_asset,
            expected_state_revision=created.state_revision,
            expected_asset_revision_id=created.assets[0].revision_id,
            actor_id="operator-1",
            reason="Update display name for atomicity test",
        )
    assert store.state_path.read_bytes() == before
    assert store.validate() == created


def test_replay_detects_tamper_reorder_truncation_and_duplicate_ids(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    _, created = _created(store)
    updated_asset = _asset().with_field_update(
        "display_name",
        "Second Revision",
        FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
    )
    updated = store.update_asset(
        updated_asset,
        expected_state_revision=created.state_revision,
        expected_asset_revision_id=created.assets[0].revision_id,
        actor_id="operator-1",
        reason="Create another auditable asset revision",
    )
    original = json.loads(store.state_path.read_text(encoding="utf-8"))

    tampered = json.loads(json.dumps(original))
    tampered["events"][0]["reason"] = "Tampered reason"
    store.state_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(PackagingLibraryAuditError, match="event_digest_invalid"):
        store.validate()

    reordered = json.loads(json.dumps(original))
    reordered["events"].reverse()
    store.state_path.write_text(json.dumps(reordered), encoding="utf-8")
    with pytest.raises(PackagingLibraryAuditError, match="chain_disconnected"):
        store.validate()

    removed_middle = json.loads(json.dumps(original))
    removed_middle["events"].pop(0)
    store.state_path.write_text(json.dumps(removed_middle), encoding="utf-8")
    with pytest.raises(PackagingLibraryAuditError, match="chain_disconnected"):
        store.validate()

    truncated = json.loads(json.dumps(original))
    truncated["events"].pop()
    store.state_path.write_text(json.dumps(truncated), encoding="utf-8")
    with pytest.raises(PackagingLibraryAuditError, match="state_mismatch|head_mismatch"):
        store.validate()

    duplicated = json.loads(json.dumps(original))
    duplicated["events"].append(duplicated["events"][-1])
    store.state_path.write_text(json.dumps(duplicated), encoding="utf-8")
    with pytest.raises(PackagingLibraryAuditError, match="event_id_duplicate"):
        store.validate()

    store.state_path.write_text(json.dumps(original), encoding="utf-8")
    assert store.validate() == updated


def test_event_identity_is_deterministic_and_sensitive_reasons_reject(tmp_path: Path) -> None:
    first = _store(tmp_path / "first-library")
    second = _store(tmp_path / "second-library")
    _, first_snapshot = _created(first)
    _, second_snapshot = _created(second)

    assert first_snapshot.events[0] == second_snapshot.events[0]
    assert first_snapshot.state_revision == second_snapshot.state_revision
    assert first_snapshot.events[0].event_id == second_snapshot.events[0].event_id
    assert str(tmp_path) not in first_snapshot.events[0].as_dict().__repr__()
    with pytest.raises(PackagingLibraryAuditError, match="reason_invalid_or_sensitive"):
        first.create_asset(
            _asset(asset_id="another-pack"),
            expected_state_revision=first_snapshot.state_revision,
            actor_id="operator-1",
            reason="Copy token=private123",
        )
    with pytest.raises(PackagingLibraryAuditError, match="reason_invalid_or_sensitive"):
        first.create_asset(
            _asset(asset_id="another-pack"),
            expected_state_revision=first_snapshot.state_revision,
            actor_id="operator-1",
            reason="Reference file C:\\supplier\\private.pdf",
        )


def test_unicode_asset_metadata_replays_using_its_canonical_revision(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    initial = store.snapshot()
    asset = _asset(display_name="Bouteille 500 mL été")
    created = store.create_asset(
        asset,
        expected_state_revision=initial.state_revision,
        actor_id="operator-1",
        reason="Store Unicode display metadata",
    )

    assert created.assets[0].revision_id == asset.revision_id
    assert store.validate() == created


def test_duplicate_relationship_is_symmetric_stable_and_revisioned(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    revisions = _relationship_assets(store)
    state = store.snapshot()
    created = store.create_relationship(
        "DUPLICATE",
        "asset-b",
        "asset-a",
        expected_state_revision=state.state_revision,
        expected_asset_revisions=(
            ("asset-a", revisions["asset-a"]),
            ("asset-b", revisions["asset-b"]),
        ),
        actor_id="operator-1",
        reason="Owner confirmed the packages are duplicates",
        provenance_class="USER_DECLARED",
        source_reference_id="owner-decision-1",
    )
    relationship = created.relationships[0]
    assert isinstance(relationship, PackagingAssetRelationship)
    assert (relationship.asset_a_id, relationship.asset_b_id) == ("asset-a", "asset-b")
    assert relationship.relationship_id.startswith("packaging-relationship:")
    assert relationship.revision_id.startswith("packaging-relationship-revision:")
    assert relationship.provenance_class == "USER_DECLARED"
    assert created.events[-1].operation_type == "RELATE"
    assert store.validate() == created

    with pytest.raises(PackagingLibraryAuditError, match="already_exists"):
        store.create_relationship(
            "DUPLICATE",
            "asset-a",
            "asset-b",
            expected_state_revision=created.state_revision,
            expected_asset_revisions=(
                ("asset-a", revisions["asset-a"]),
                ("asset-b", revisions["asset-b"]),
            ),
            actor_id="operator-2",
            reason="Repeat duplicate relation",
        )
    removed = store.remove_relationship(
        relationship.relationship_id,
        expected_state_revision=created.state_revision,
        expected_relationship_revision_id=relationship.revision_id,
        actor_id="operator-1",
        reason="Owner withdrew the duplicate declaration",
    )
    assert removed.relationships == ()
    assert removed.events[-1].operation_type == "UNRELATE"
    assert store.validate() == removed

    restored = store.create_relationship(
        "DUPLICATE",
        "asset-a",
        "asset-b",
        expected_state_revision=removed.state_revision,
        expected_asset_revisions=(
            ("asset-a", revisions["asset-a"]),
            ("asset-b", revisions["asset-b"]),
        ),
        actor_id="operator-1",
        reason="Owner reconfirmed the duplicate declaration",
    )
    assert restored.relationships[0].relationship_id == relationship.relationship_id
    assert restored.relationships[0].revision_id != relationship.revision_id
    assert store.validate() == restored

    state_value = json.loads(store.state_path.read_text(encoding="utf-8"))
    state_value["relationships"][0]["provenance_class"] = "PACKLAB_ESTIMATE"
    store.state_path.write_text(json.dumps(state_value), encoding="utf-8")
    with pytest.raises(PackagingLibraryAuditError, match="relationship_revision_invalid"):
        store.snapshot()


def test_variant_relationships_reject_self_cycles_and_stale_asset_revisions(
    tmp_path: Path,
) -> None:
    store = _store(tmp_path / "library")
    revisions = _relationship_assets(store)

    def link(parent: str, child: str):
        snapshot = store.snapshot()
        return store.create_relationship(
            "VARIANT",
            parent,
            child,
            expected_state_revision=snapshot.state_revision,
            expected_asset_revisions=((parent, revisions[parent]), (child, revisions[child])),
            actor_id="operator-1",
            reason="Owner declared packaging variant relationship",
        )

    link("asset-a", "asset-b")
    second = link("asset-b", "asset-c")
    assert sorted((item.asset_a_id, item.asset_b_id) for item in second.relationships) == [
        ("asset-a", "asset-b"),
        ("asset-b", "asset-c"),
    ]
    with pytest.raises(PackagingLibraryAuditError, match="self_link"):
        link("asset-a", "asset-a")
    with pytest.raises(PackagingLibraryAuditError, match="cycle_invalid"):
        link("asset-c", "asset-a")

    snapshot = store.snapshot()
    with pytest.raises(StalePackagingLibraryState, match="asset_revision_stale"):
        store.create_relationship(
            "DUPLICATE",
            "asset-a",
            "asset-c",
            expected_state_revision=snapshot.state_revision,
            expected_asset_revisions=(
                ("asset-a", "packaging-asset:" + "0" * 64),
                ("asset-c", revisions["asset-c"]),
            ),
            actor_id="operator-1",
            reason="Try relation with an obsolete asset revision",
        )
    assert store.validate() == second


def test_schema_one_state_without_relationships_remains_readable(tmp_path: Path) -> None:
    store = _store(tmp_path / "library")
    _, created = _created(store)
    state_value = json.loads(store.state_path.read_text(encoding="utf-8"))
    state_value["schema_version"] = 1
    state_value.pop("relationships", None)
    store.state_path.write_text(json.dumps(state_value), encoding="utf-8")

    migrated = store.snapshot()
    assert migrated.relationships == ()
    assert migrated.state_revision == created.state_revision
    assert migrated.assets == created.assets
