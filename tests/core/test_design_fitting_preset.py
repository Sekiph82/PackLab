from __future__ import annotations

import json
from dataclasses import replace

import pytest
from tests.core.test_symmetric_section_loft import _scan_master

from packlab_core.design_fitting_preset import (
    FITTING_PRESET_CONTRACT,
    DesignFittingPreset,
    FittingPresetError,
    PackageFamilyFittingDefaults,
    apply_fitting_preset,
)
from packlab_core.design_model import PackageFamily


def test_fitting_preset_round_trip_is_canonical_and_contains_no_scan_geometry() -> None:
    preset = DesignFittingPreset()
    serialized = preset.canonical_bytes()
    restored = DesignFittingPreset.from_json(serialized)
    reordered = json.dumps(preset.as_dict(), sort_keys=False, separators=(",", ":")).encode()

    assert restored == preset
    assert restored.canonical_bytes() == serialized
    assert preset.serialize().encode("utf-8") == serialized
    assert json.loads(serialized) == json.loads(reordered)
    assert preset.as_dict()["contract"] == FITTING_PRESET_CONTRACT
    assert preset.as_dict()["raw_scan_embedded"] is False
    assert preset.as_dict()["fit_quality_claimed"] is False
    assert preset.as_dict()["scan_master_revision_id"] is None
    assert preset.as_dict()["scan_master_geometry_sha256"] is None
    assert b"scan-master-section" not in serialized
    assert b'"mesh"' not in serialized
    assert b'"geometry"' not in serialized
    assert len(preset.digest) == 64


def test_apply_recomputes_evidence_for_new_parent_without_reusing_fit_claims() -> None:
    preset = DesignFittingPreset()
    first_scan = _scan_master(shape="ellipse")
    second_scan = _scan_master(shape="rounded_rect")
    first = apply_fitting_preset(
        preset,
        first_scan,
        expected_scan_master_revision_id=first_scan.revision_id,
        package_family=PackageFamily.BOTTLE,
        actor_id="operator-1",
        reason="Apply fitting defaults to first scan.",
        created_at_utc="2026-10-03T17:00:00Z",
    )
    second = apply_fitting_preset(
        preset,
        second_scan,
        expected_scan_master_revision_id=second_scan.revision_id,
        package_family=PackageFamily.JAR,
        actor_id="operator-1",
        reason="Apply fitting defaults to second scan.",
        created_at_utc="2026-10-03T17:00:00Z",
    )

    assert first.recommendation.scan_master_revision_id == first_scan.revision_id
    assert second.recommendation.scan_master_revision_id == second_scan.revision_id
    assert first.recommendation.recommendation_id != second.recommendation.recommendation_id
    assert (
        first.recommendation.parent_binding.revision_id
        != second.recommendation.parent_binding.revision_id
    )
    assert (
        first.recommendation.parent_binding.fitted_to_scan_master_revision_id
        == first_scan.revision_id
    )
    assert (
        second.recommendation.parent_binding.fitted_to_scan_master_revision_id
        == second_scan.revision_id
    )
    assert first.preset_digest == second.preset_digest == preset.digest
    assert first.package_defaults.package_family is PackageFamily.BOTTLE
    assert second.package_defaults.package_family is PackageFamily.JAR
    assert first.as_dict()["fit_quality_claimed"] is False
    assert first.as_dict()["raw_scan_embedded"] is False
    assert first.as_dict()["fitting_strategy_recommendation"]["is_design_model_fit"] is False


def test_preset_rejects_unsupported_versions_stale_parents_and_unknown_fields() -> None:
    preset = DesignFittingPreset()
    unsupported = preset.as_dict()
    unsupported["version"] = 99
    with pytest.raises(FittingPresetError, match="unsupported_fitting_preset_version"):
        DesignFittingPreset.from_json(json.dumps(unsupported))

    unknown = preset.as_dict()
    unknown["private_scan_path"] = "local/scans/customer.ply"
    with pytest.raises(FittingPresetError, match="preset_fields_unsupported_or_missing"):
        DesignFittingPreset.from_json(json.dumps(unknown))

    scan = _scan_master()
    with pytest.raises(FittingPresetError, match="selected_scan_master_parent_stale"):
        apply_fitting_preset(
            preset,
            scan,
            expected_scan_master_revision_id="different-revision",
            package_family=PackageFamily.BOTTLE,
            actor_id="operator-1",
            reason="Reject stale parent.",
            created_at_utc="2026-10-03T17:00:00Z",
        )


def test_preset_rejects_duplicate_keys_invalid_constraints_and_incomplete_defaults() -> None:
    with pytest.raises(FittingPresetError, match="duplicate_json_key"):
        DesignFittingPreset.from_json('{"contract":"x","contract":"y"}')

    with pytest.raises(FittingPresetError, match="transition_fractions_must_be_ordered"):
        PackageFamilyFittingDefaults(
            PackageFamily.BOTTLE,
            base_transition_fraction=0.7,
            shoulder_transition_fraction=0.6,
        )

    incomplete = tuple(
        item
        for item in DesignFittingPreset().package_defaults
        if item.package_family is not PackageFamily.OTHER
    )
    with pytest.raises(FittingPresetError, match="package_family_defaults_incomplete_or_duplicate"):
        replace(DesignFittingPreset(), package_defaults=incomplete)
