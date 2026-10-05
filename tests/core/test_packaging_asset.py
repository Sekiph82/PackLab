from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from packlab_core.packaging_asset import (
    AssetStatus,
    BaseMaterial,
    ClosureType,
    DesignModelLink,
    FieldProvenance,
    MeasurementUnit,
    PackagingAsset,
    PackagingAssetError,
    PackagingFamily,
    PackagingMeasurement,
    ProvenanceClass,
    RawScanLink,
    ScanMasterLink,
)
from packlab_core.reconstruction import ScaleState


def _asset(**overrides: object) -> PackagingAsset:
    values: dict[str, object] = {
        "asset_id": "kenya-pack-001",
        "display_name": "500 mL water bottle",
        "family": PackagingFamily.BOTTLE,
        "nominal_volume": PackagingMeasurement(500, MeasurementUnit.MILLILITER),
        "supplier_id": "supplier-001",
        "supplier_name": "Example Supplier",
        "base_material": BaseMaterial.PET,
        "empty_package_weight": PackagingMeasurement(18.5, MeasurementUnit.GRAM),
        "overall_height": PackagingMeasurement(210, MeasurementUnit.MILLIMETER),
        "body_diameter": PackagingMeasurement(62, MeasurementUnit.MILLIMETER),
        "neck_finish": "28/410",
        "neck_finish_diameter": PackagingMeasurement(28, MeasurementUnit.MILLIMETER),
        "closure_type": ClosureType.SCREW_CAP,
        "status": AssetStatus.ACTIVE,
    }
    values.update(overrides)
    if "field_provenance" not in values:
        field_names = (
            "display_name",
            "family",
            "nominal_volume",
            "supplier_id",
            "supplier_name",
            "base_material",
            "other_family_label",
            "other_material_label",
            "empty_package_weight",
            "overall_height",
            "body_diameter",
            "neck_finish",
            "neck_finish_diameter",
            "closure_type",
            "closure_description",
            "status",
        )
        values["field_provenance"] = tuple(
            FieldProvenance(
                field_name,
                ProvenanceClass.UNKNOWN
                if value is None or getattr(value, "value", None) == "UNKNOWN"
                else ProvenanceClass.USER_DECLARED,
            )
            for field_name in field_names
            if (value := values.get(field_name)) is not None
            or getattr(values.get(field_name), "value", None) == "UNKNOWN"
        )
    return PackagingAsset(**values)  # type: ignore[arg-type]


@pytest.mark.parametrize("family", list(PackagingFamily))
def test_packaging_asset_accepts_bounded_families_and_explicit_unknowns(
    family: PackagingFamily,
) -> None:
    overrides: dict[str, object] = {"family": family}
    if family is PackagingFamily.OTHER:
        overrides["other_family_label"] = "Refill cartridge"
    known = _asset(**overrides)
    assert known.family is family

    unknown = _asset(
        family=PackagingFamily.UNKNOWN,
        nominal_volume=None,
        supplier_id=None,
        supplier_name=None,
        base_material=BaseMaterial.UNKNOWN,
        empty_package_weight=None,
        overall_height=None,
        body_diameter=None,
        neck_finish=None,
        neck_finish_diameter=None,
        closure_type=ClosureType.UNKNOWN,
        status=AssetStatus.UNKNOWN,
    )

    assert unknown.nominal_volume is None
    assert unknown.empty_package_weight is None
    assert unknown.as_dict()["supplier"] == {"supplier_id": None, "name": None}
    assert unknown.as_dict()["base_material"] == "UNKNOWN"
    assert unknown.as_dict()["status"] == "UNKNOWN"
    assert unknown.as_dict()["physical_accuracy_verified"] is False


def test_other_family_and_material_require_explicit_bounded_labels() -> None:
    asset = _asset(
        family=PackagingFamily.OTHER,
        other_family_label="Refill cartridge",
        base_material=BaseMaterial.OTHER,
        other_material_label="Plant fiber composite",
    )

    assert asset.as_dict()["other_family_label"] == "Refill cartridge"
    assert asset.as_dict()["other_material_label"] == "Plant fiber composite"
    with pytest.raises(PackagingAssetError, match="other_family_label_invalid"):
        _asset(family=PackagingFamily.OTHER)
    with pytest.raises(PackagingAssetError, match="other_material_label_invalid"):
        _asset(base_material=BaseMaterial.OTHER)


def test_serialization_and_revision_are_deterministic_and_path_free() -> None:
    first = _asset()
    second = _asset()

    assert first.canonical_json == second.canonical_json
    assert first.revision_id == second.revision_id
    assert first.revision_id.startswith("packaging-asset:")
    assert "C:\\" not in first.canonical_json
    assert "project_root" not in first.as_dict()
    assert json.loads(first.canonical_json) == first.as_dict()


def test_each_metadata_change_creates_a_distinct_content_revision() -> None:
    assert (
        _asset(display_name="500 mL bottle").revision_id
        != _asset(display_name="1 L bottle").revision_id
    )


def test_asset_values_are_immutable() -> None:
    with pytest.raises(FrozenInstanceError):
        _asset().display_name = "Changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("asset_id", "../private", "asset_id_invalid"),
        ("asset_id", "C:\\owner\\asset", "asset_id_invalid"),
        ("display_name", "  ", "display_name_invalid"),
        ("display_name", "x" * 121, "display_name_invalid"),
        ("display_name", "C:\\private\\supplier.xlsx", "display_name_invalid"),
        ("family", "BOTTLE", "family_invalid"),
        ("base_material", "PET", "base_material_invalid"),
        ("closure_type", "PUMP", "closure_type_invalid"),
        ("status", "ACTIVE", "status_invalid"),
        ("supplier_name", None, "supplier_identity_incomplete"),
        ("supplier_name", "https://supplier.example", "supplier_name_invalid"),
        (
            "nominal_volume",
            PackagingMeasurement(10, MeasurementUnit.GRAM),
            "nominal_volume_unit_invalid",
        ),
        (
            "empty_package_weight",
            PackagingMeasurement(10, MeasurementUnit.MILLILITER),
            "empty_package_weight_unit_invalid",
        ),
        (
            "overall_height",
            PackagingMeasurement(10, MeasurementUnit.KILOGRAM),
            "overall_height_unit_invalid",
        ),
    ],
)
def test_invalid_ids_enums_supplier_pairs_and_units_reject(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(PackagingAssetError, match=message):
        _asset(**{field: value})


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), True, 1e100])
def test_measurements_reject_nonpositive_nonfinite_or_unbounded_values(value: object) -> None:
    with pytest.raises(PackagingAssetError, match="measurement_value_invalid"):
        PackagingMeasurement(value, MeasurementUnit.MILLILITER)  # type: ignore[arg-type]


def test_unknown_measurement_is_distinct_from_numeric_zero() -> None:
    unknown = _asset(nominal_volume=None)
    with pytest.raises(PackagingAssetError, match="measurement_value_invalid"):
        PackagingMeasurement(0, MeasurementUnit.MILLILITER)
    assert unknown.nominal_volume is None


def test_supplier_fact_and_packlab_estimate_remain_distinct_and_noncertifying() -> None:
    supplier_fact = FieldProvenance(
        "nominal_volume",
        ProvenanceClass.SUPPLIER_FACT,
        source_reference_id="supplier-sheet-17",
        source_description="Supplier product specification",
    )
    estimate = FieldProvenance(
        "empty_package_weight",
        ProvenanceClass.PACKLAB_ESTIMATE,
        method_id="weighing-estimator.v1",
        confidence=0.72,
    )
    asset = _asset(
        field_provenance=_provenance_tuple(_base_user_provenance(), supplier_fact, estimate)
    )

    serialized = asset.as_dict()
    provenance = {item["field_name"]: item for item in serialized["field_provenance"]}
    assert provenance["nominal_volume"]["classification"] == "SUPPLIER_FACT"
    assert provenance["nominal_volume"]["source_reference_id"] == "supplier-sheet-17"
    assert provenance["empty_package_weight"]["classification"] == "PACKLAB_ESTIMATE"
    assert provenance["empty_package_weight"]["method_id"] == "weighing-estimator.v1"
    assert provenance["empty_package_weight"]["confidence"] == 0.72
    assert serialized["supplier_certification_inferred"] is False
    assert serialized["physical_accuracy_verified"] is False
    assert serialized["manufacturing_authorized"] is False


def test_provenance_is_required_for_populated_fields_and_unknown_is_explicit() -> None:
    provenance = list(_base_user_provenance())
    provenance.remove(next(item for item in provenance if item.field_name == "nominal_volume"))
    with pytest.raises(PackagingAssetError, match="nominal_volume_provenance_required"):
        _asset(field_provenance=tuple(provenance))

    unknown = _asset(
        nominal_volume=None,
        field_provenance=_provenance_tuple(
            _base_user_provenance(),
            FieldProvenance("nominal_volume", ProvenanceClass.UNKNOWN),
        ),
    )
    assert (
        next(
            item["classification"]
            for item in unknown.as_dict()["field_provenance"]
            if item["field_name"] == "nominal_volume"
        )
        == "UNKNOWN"
    )


def test_provenance_input_order_does_not_change_canonical_revision() -> None:
    provenance = _base_user_provenance()
    forward = _asset(field_provenance=provenance)
    reverse = _asset(field_provenance=tuple(reversed(provenance)))

    assert forward.field_provenance == reverse.field_provenance
    assert forward.canonical_json == reverse.canonical_json
    assert forward.revision_id == reverse.revision_id


def test_edit_creates_immutable_successor_revision_and_preserves_prior_record() -> None:
    original = _asset()
    successor = original.with_field_update(
        "nominal_volume",
        PackagingMeasurement(750, MeasurementUnit.MILLILITER),
        FieldProvenance(
            "nominal_volume",
            ProvenanceClass.PACKLAB_ESTIMATE,
            method_id="capacity-inference.v2",
            confidence=0.65,
        ),
    )

    assert original.nominal_volume == PackagingMeasurement(500, MeasurementUnit.MILLILITER)
    assert original.revision_id != successor.revision_id
    assert successor.nominal_volume == PackagingMeasurement(750, MeasurementUnit.MILLILITER)
    assert (
        next(
            item["classification"]
            for item in successor.as_dict()["field_provenance"]
            if item["field_name"] == "nominal_volume"
        )
        == "PACKLAB_ESTIMATE"
    )


def test_provenance_rejects_bad_authority_combinations_and_invalid_edits() -> None:
    with pytest.raises(PackagingAssetError, match="supplier_fact_provenance_invalid"):
        FieldProvenance("nominal_volume", ProvenanceClass.SUPPLIER_FACT)
    with pytest.raises(PackagingAssetError, match="estimate_provenance_invalid"):
        FieldProvenance(
            "nominal_volume",
            ProvenanceClass.PACKLAB_ESTIMATE,
            source_reference_id="supplier-source-1",
            method_id="volume-estimator.v1",
        )
    with pytest.raises(PackagingAssetError, match="confidence_invalid"):
        FieldProvenance(
            "nominal_volume",
            ProvenanceClass.PACKLAB_ESTIMATE,
            method_id="volume-estimator.v1",
            confidence=1.01,
        )
    with pytest.raises(PackagingAssetError, match="field_not_editable"):
        _asset().with_field_update(
            "asset_id",
            "another-id",
            FieldProvenance("display_name", ProvenanceClass.USER_DECLARED),
        )
    with pytest.raises(PackagingAssetError, match="field_provenance_mismatch"):
        _asset().with_field_update(
            "nominal_volume",
            PackagingMeasurement(750, MeasurementUnit.MILLILITER),
            FieldProvenance("empty_package_weight", ProvenanceClass.USER_DECLARED),
        )


def test_source_links_are_exact_deterministic_references_and_successor_revision() -> None:
    project_a = "a1111111-1111-4111-8111-111111111111"
    project_b = "b2222222-2222-4222-8222-222222222222"
    raw_a = RawScanLink(project_a, "capture-a", "a" * 64)
    raw_b = RawScanLink(project_b, "capture-b", "b" * 64)
    scan_master = ScanMasterLink(
        project_a,
        "scan-master-1",
        "c" * 64,
        ScaleState.METRIC_UNVERIFIED,
        "scale-provenance-1",
    )
    design_model = DesignModelLink(
        project_id=project_a,
        revision_id="design-model-1",
        content_sha256="d" * 64,
        parent_authority_kind="CAPTURED_SCAN_MASTER",
        parent_authority_revision_id="scan-master-1",
        scan_master_revision_id="scan-master-1",
        scan_master_geometry_sha256="c" * 64,
        scale_state=ScaleState.METRIC_UNVERIFIED,
    )
    standalone_model = DesignModelLink(
        project_id=project_b,
        revision_id="design-model-2",
        content_sha256="e" * 64,
        parent_authority_kind="STANDALONE_DESIGN_GEOMETRY",
        parent_authority_revision_id="standalone-root-2",
        scale_state=ScaleState.RELATIVE,
    )
    original = _asset()
    linked = original.with_source_links(
        raw_scan_links=(raw_b, raw_a),
        scan_master_link=scan_master,
        design_model_links=(design_model, standalone_model),
        preferred_design_model_revision_id="design-model-2",
    )
    reverse_raw = original.with_source_links(
        raw_scan_links=(raw_a, raw_b),
        scan_master_link=scan_master,
        design_model_links=(design_model, standalone_model),
        preferred_design_model_revision_id="design-model-2",
    )

    assert linked.revision_id != original.revision_id
    assert linked.revision_id == reverse_raw.revision_id
    assert linked.raw_scan_links == (raw_a, raw_b)
    assert linked.design_model_links == (design_model, standalone_model)
    assert linked.preferred_design_model_revision_id == "design-model-2"
    assert linked.as_dict()["source_links"]["scan_master"]["mold_use_authorized"] is False
    assert "project_root" not in linked.canonical_json
    assert "vertices" not in linked.canonical_json
    assert original.raw_scan_links == ()


def test_source_links_reject_duplicate_malformed_and_stale_identities() -> None:
    project = "a1111111-1111-4111-8111-111111111111"
    raw = RawScanLink(project, "capture-1", "a" * 64)
    model = DesignModelLink(
        project_id=project,
        revision_id="design-model-1",
        content_sha256="b" * 64,
        parent_authority_kind="STANDALONE_DESIGN_GEOMETRY",
        parent_authority_revision_id="standalone-root-1",
        scale_state=ScaleState.METRIC_UNVERIFIED,
    )

    with pytest.raises(PackagingAssetError, match="raw_scan_link_duplicate"):
        _asset(raw_scan_links=(raw, raw))
    with pytest.raises(PackagingAssetError, match="design_model_link_duplicate"):
        _asset(design_model_links=(model, model))
    with pytest.raises(PackagingAssetError, match="preferred_design_model_missing"):
        _asset(design_model_links=(model,), preferred_design_model_revision_id="missing-model")
    with pytest.raises(PackagingAssetError, match="raw_scan_digest_invalid"):
        RawScanLink(project, "capture-1", "not-a-digest")
    with pytest.raises(PackagingAssetError, match="scan_master_authority_invalid"):
        ScanMasterLink(
            project,
            "scan-master-1",
            "c" * 64,
            ScaleState.METRIC_UNVERIFIED,
            "scale-provenance-1",
            mold_use_authorized=True,
        )
    with pytest.raises(PackagingAssetError, match="standalone_model_has_scan_master"):
        DesignModelLink(
            project_id=project,
            revision_id="design-model-standalone",
            content_sha256="d" * 64,
            parent_authority_kind="STANDALONE_DESIGN_GEOMETRY",
            parent_authority_revision_id="standalone-root-1",
            scale_state=ScaleState.RELATIVE,
            scan_master_revision_id="invented-scan",
        )


def _base_user_provenance() -> tuple[FieldProvenance, ...]:
    return _asset().field_provenance


def _provenance_tuple(
    base: tuple[FieldProvenance, ...], *updates: FieldProvenance
) -> tuple[FieldProvenance, ...]:
    by_field = {item.field_name: item for item in base}
    by_field.update({item.field_name: item for item in updates})
    return tuple(by_field[name] for name in sorted(by_field))
