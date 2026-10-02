from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from packlab_core.physical_accuracy_benchmark import (
    BenchmarkEnvironment,
    PhysicalBenchmarkError,
    PhysicalBenchmarkSample,
    blank_physical_benchmark_record,
    serialize_physical_benchmark_record,
)


def test_public_template_matches_executable_blank_record_and_schema() -> None:
    repository_root = Path(__file__).parents[2]
    template_path = (
        repository_root
        / "docs"
        / "calibration"
        / "benchmarks"
        / "physical-benchmark-record-template.json"
    )
    schema_path = (
        repository_root
        / "docs"
        / "calibration"
        / "benchmarks"
        / "physical-benchmark-record.schema.json"
    )
    template = json.loads(template_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(template)
    record = blank_physical_benchmark_record()
    assert template == record.as_dict()
    assert schema["properties"]["record_version"]["const"] == record.record_version
    assert schema["properties"]["acceptance_thresholds"]["type"] == "null"
    assert schema["properties"]["benchmark_categories_required"]["const"] == list(
        template["benchmark_categories_required"]
    )
    assert set(schema["required"]).issubset(template)
    assert set(template).issubset(schema["properties"])
    assert set(schema["$defs"]["sample"]["required"]) == set(template["samples"][0])


def test_blank_template_has_missing_ground_truth_and_owner_required_status() -> None:
    record = blank_physical_benchmark_record()
    assert record.record_status == "OWNER_REQUIRED"
    assert {sample.category for sample in record.samples} == {
        "matte_bottle",
        "glossy_bottle",
        "jerrycan",
    }
    assert all(sample.disposition == "MISSING_MEASUREMENT" for sample in record.samples)
    assert all(sample.ground_truth is None for sample in record.samples)
    assert all(sample.measurement_id is None for sample in record.samples)


def test_accepted_sample_requires_caliper_ground_truth_and_revision_links() -> None:
    with pytest.raises(PhysicalBenchmarkError, match="ground_truth_or_links_missing"):
        PhysicalBenchmarkSample(
            "SAMPLE-MATTE-001",
            "matte_bottle",
            "ACCEPTED",
            "scan-001",
            "scan-revision-1",
            None,
            None,
            "ref:private-evidence-1",
            None,
            None,
        )


def test_rejected_samples_are_retained_in_record_digest_and_serialization() -> None:
    blank = blank_physical_benchmark_record()
    rejected = PhysicalBenchmarkSample(
        "SAMPLE-MATTE-REJECTED-001",
        "matte_bottle",
        "REJECTED",
        "scan-rejected-001",
        "scan-revision-1",
        "measurement-rejected-001",
        "measurement-revision-1",
        "sha256:" + "a" * 64,
        None,
        "Capture was rejected by the owner for recorded review.",
    )
    record = replace(blank, samples=(*blank.samples, rejected))
    reversed_record = replace(record, samples=tuple(reversed(record.samples)))
    encoded = serialize_physical_benchmark_record(record).decode("utf-8")
    assert len(record.samples) == 4
    assert "SAMPLE-MATTE-REJECTED-001" in encoded
    assert "Capture was rejected by the owner" in encoded
    assert record.record_digest != blank.record_digest
    assert record.record_digest == reversed_record.record_digest


def test_privacy_safe_references_reject_paths_and_ambient_identity() -> None:
    blank = blank_physical_benchmark_record()
    with pytest.raises(PhysicalBenchmarkError, match="evidence_reference_unsafe"):
        bad_sample = replace(blank.samples[0], evidence_reference="C:/private/scan.jpg")
        replace(blank, samples=(bad_sample, *blank.samples[1:]))
    with pytest.raises(PhysicalBenchmarkError, match="operator_reference_unsafe"):
        replace(blank, operator_reference="owner@example.com")
    with pytest.raises(PhysicalBenchmarkError, match="environment_lighting_description_invalid"):
        BenchmarkEnvironment(lighting_description="owner@example.com")


def test_record_digest_is_deterministic_and_contains_no_measured_values_or_thresholds() -> None:
    first = blank_physical_benchmark_record()
    second = blank_physical_benchmark_record()
    assert first.record_digest == second.record_digest
    assert serialize_physical_benchmark_record(first) == serialize_physical_benchmark_record(second)
    payload = first.as_dict()
    assert payload["acceptance_thresholds"] is None
    assert payload["threshold_status"] == "NOT_DEFINED_BY_PROTOCOL"
    assert payload["synthetic_evidence_is_physical_evidence"] is False
    assert all(sample["ground_truth"] is None for sample in payload["samples"])
    assert all(sample["disposition"] == "MISSING_MEASUREMENT" for sample in payload["samples"])


def test_ready_for_audit_is_blocked_by_missing_measurement_or_environment() -> None:
    blank = blank_physical_benchmark_record()
    with pytest.raises(PhysicalBenchmarkError, match="missing_measurement_blocks_ready_status"):
        replace(
            blank,
            record_id="BENCH-UNRECORDED-EXAMPLE",
            record_status="READY_FOR_AUDIT",
        )
