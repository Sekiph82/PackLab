from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest

from packlab_core.capabilities import Capability, CapabilityStatus
from packlab_core.feature_extraction import FeatureExtractionConfig
from packlab_core.matching import MatcherSelectionConfig
from packlab_core.reconstruction import ReconstructionJobSpec
from packlab_core.reconstruction_preset import (
    CPU_SAFE_RESOURCE_PRESET,
    GPU_AWARE_RESOURCE_PRESET,
    PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET,
    RECONSTRUCTION_PRESET_CONTRACT,
    GPUUnavailableError,
    ReconstructionPreset,
    ReconstructionPresetError,
    ResourceBudgetExceededError,
    ResourceCapabilitySnapshot,
    ResourceEstimates,
    ResourceExecutionMode,
    ResourceLimits,
    ResourcePlanOutcome,
    UnsupportedReconstructionPresetOption,
)
from packlab_core.sparse_mapping import SparseMappingConfig


def test_packaged_preset_is_explicit_typed_and_disclaims_authority() -> None:
    preset = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET

    assert preset.preset_identity == "packaged-consumer-goods-reconstruction:1"
    assert isinstance(preset.feature_extraction, FeatureExtractionConfig)
    assert isinstance(preset.matcher, MatcherSelectionConfig)
    assert isinstance(preset.sparse_mapping, SparseMappingConfig)
    text = json.dumps(preset.to_dict())
    assert "physical benchmark evidence" in text
    assert "universal optimum" in text
    assert "METRIC_VERIFIED" in text
    assert "filesystem materialization" in text
    assert "CAD authority" in text
    assert preset.resource_policy.policy_identity == "cpu-safe:1"
    assert preset.configuration_view()["resource_policy"]["policy_identity"] == "cpu-safe:1"


def test_named_resource_presets_are_versioned_and_truthful() -> None:
    assert CPU_SAFE_RESOURCE_PRESET.execution_mode is ResourceExecutionMode.CPU_ONLY
    assert GPU_AWARE_RESOURCE_PRESET.execution_mode is ResourceExecutionMode.GPU_PREFERRED
    assert CPU_SAFE_RESOURCE_PRESET.policy_identity == "cpu-safe:1"
    assert GPU_AWARE_RESOURCE_PRESET.policy_identity == "gpu-aware:1"
    for preset in (CPU_SAFE_RESOURCE_PRESET, GPU_AWARE_RESOURCE_PRESET):
        encoded = json.dumps(preset.to_dict()).lower()
        assert "not hardware benchmarks" in encoded
        assert "does not inspect hardware" in encoded
        assert len(preset.digest) == 64


@pytest.mark.parametrize(
    "kwargs",
    [
        {"input_bytes": True},
        {"working_set_bytes": 0},
        {"retained_output_bytes": 65 * 1024**3},
        {"parallel_workers": 65},
        {"input_bytes": 9 * 1024**3, "working_set_bytes": 8 * 1024**3},
        {"retained_output_bytes": 9 * 1024**3, "working_set_bytes": 8 * 1024**3},
    ],
)
def test_resource_limits_reject_type_overflow_and_inconsistent_values(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ReconstructionPresetError):
        ResourceLimits(**kwargs)  # type: ignore[arg-type]


def test_resource_estimates_are_immutable_and_reject_boolean_or_missing_fields() -> None:
    estimates = ResourceEstimates(1, 2, 1, 1)
    with pytest.raises((AttributeError, TypeError)):
        estimates.input_bytes = 2  # type: ignore[misc]
    with pytest.raises(ReconstructionPresetError):
        ResourceEstimates(True, 2, 1, 1)  # type: ignore[arg-type]
    with pytest.raises(ReconstructionPresetError):
        ResourceEstimates.from_mapping({"input_bytes": 1})


def test_capability_snapshot_is_explicit_and_does_not_infer_from_driver_labels() -> None:
    snapshot = ResourceCapabilitySnapshot(
        {
            "nvidia_driver": Capability(
                "nvidia_driver", CapabilityStatus.AVAILABLE, "550", "driver label", "reported"
            )
        }
    )
    plan = GPU_AWARE_RESOURCE_PRESET.resolve(snapshot, ResourceEstimates(1, 2, 1, 1))

    assert plan.capability_status is CapabilityStatus.UNKNOWN
    assert plan.outcome is ResourcePlanOutcome.CPU_FALLBACK
    assert plan.selected_mode is ResourceExecutionMode.CPU_ONLY
    assert "explicit CUDA capability" in (plan.fallback_reason or "")
    assert "capability snapshot has no explicit CUDA record" in plan.capability_provenance


def test_direct_cuda_capability_selects_gpu_and_preserves_provenance() -> None:
    snapshot = ResourceCapabilitySnapshot(
        {
            "cuda": Capability(
                "cuda",
                CapabilityStatus.AVAILABLE,
                "12.4",
                "direct CUDA toolkit probe: nvcc --version",
                "exit code 0",
            )
        }
    )
    plan = GPU_AWARE_RESOURCE_PRESET.resolve(
        ResourceCapabilitySnapshot(snapshot.records),
        {
            "input_bytes": 1,
            "working_set_bytes": 2,
            "retained_output_bytes": 1,
            "parallel_workers": 1,
        },
    )

    assert plan.outcome is ResourcePlanOutcome.GPU_SELECTED
    assert plan.selected_mode is ResourceExecutionMode.GPU_PREFERRED
    assert plan.capability_status is CapabilityStatus.AVAILABLE
    assert plan.capability_provenance == "direct CUDA toolkit probe: nvcc --version"
    assert plan.capability_version == "12.4"


def test_gpu_required_fails_closed_when_cuda_is_unknown() -> None:
    required = replace(GPU_AWARE_RESOURCE_PRESET, execution_mode=ResourceExecutionMode.GPU_REQUIRED)
    with pytest.raises(GPUUnavailableError) as error:
        required.resolve(ResourceCapabilitySnapshot({}), ResourceEstimates(1, 2, 1, 1))
    assert error.value.outcome is ResourcePlanOutcome.GPU_UNAVAILABLE


def test_over_budget_is_rejected_before_plan_creation() -> None:
    estimates = ResourceEstimates(17 * 1024**3, 17 * 1024**3, 1, 1)
    with pytest.raises(ResourceBudgetExceededError) as error:
        GPU_AWARE_RESOURCE_PRESET.resolve(ResourceCapabilitySnapshot({}), estimates)
    assert error.value.outcome is ResourcePlanOutcome.OVER_BUDGET
    assert error.value.resource_name == "input_bytes"
    assert error.value.limit == GPU_AWARE_RESOURCE_PRESET.limits.input_bytes


def test_equivalent_resource_inputs_have_identical_plan_serialization_and_digest() -> None:
    snapshot = ResourceCapabilitySnapshot(
        {
            "cuda": Capability(
                "cuda", CapabilityStatus.UNKNOWN, None, "test snapshot", "not available"
            )
        }
    )
    first = GPU_AWARE_RESOURCE_PRESET.resolve(
        snapshot,
        {
            "input_bytes": 1,
            "working_set_bytes": 2,
            "retained_output_bytes": 1,
            "parallel_workers": 1,
        },
    )
    second = GPU_AWARE_RESOURCE_PRESET.resolve(
        ResourceCapabilitySnapshot(dict(snapshot.records)),
        ResourceEstimates(1, 2, 1, 1),
    )

    assert first.serialize() == second.serialize()
    assert first.digest == second.digest


def test_preset_is_immutable_and_overrides_do_not_mutate_parent() -> None:
    preset = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET
    updated = preset.with_overrides(
        {
            "feature_extraction": {"feature_count_limit": 20_000},
            "matcher": {"overlap": 3},
            "sparse_mapping": {"sparse_output_asset_id": "working/reconstruction/custom"},
        }
    )

    assert updated.feature_extraction.feature_count_limit == 20_000
    assert updated.matcher.overlap == 3
    assert updated.sparse_mapping.sparse_output_asset_id.endswith("custom")
    assert preset.feature_extraction.feature_count_limit == 12_000
    assert preset.matcher.overlap == 2
    assert preset.sparse_mapping.sparse_output_asset_id.endswith("sparse")
    with pytest.raises((AttributeError, TypeError)):
        preset.preset_id = "other"  # type: ignore[misc]


def test_equivalent_nested_mapping_order_has_identical_serialization_and_digest() -> None:
    first = ReconstructionPreset.from_overrides(
        {
            "sparse_mapping": {
                "database_asset_id": "working/reconstruction/database.db",
                "image_path_asset_id": "working/images",
            },
            "feature_extraction": {
                "feature_count_limit": 16_000,
                "peak_threshold": 0.005,
            },
            "matcher": {"window_size": 6, "overlap": 3},
        }
    )
    second = ReconstructionPreset.from_overrides(
        {
            "matcher": {"overlap": 3, "window_size": 6},
            "feature_extraction": {
                "peak_threshold": 0.005,
                "feature_count_limit": 16_000,
            },
            "sparse_mapping": {
                "image_path_asset_id": "working/images",
                "database_asset_id": "working/reconstruction/database.db",
            },
        }
    )

    assert first.serialize() == second.serialize()
    assert first.configuration_digest() == second.configuration_digest()


def test_canonical_json_is_utf8_safe_and_digest_matches_bytes() -> None:
    preset = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET
    serialized = preset.serialize()

    assert serialized == json.dumps(
        preset.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=True
    )
    assert serialized.encode("utf-8")
    assert preset.digest == hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def test_configuration_view_is_immutable_and_compatible_with_job_spec() -> None:
    preset = PACKAGED_CONSUMER_GOODS_RECONSTRUCTION_PRESET
    view = preset.configuration_view()
    assert view["contract"] == RECONSTRUCTION_PRESET_CONTRACT
    assert view["configuration_digest"] == preset.digest
    with pytest.raises(TypeError):
        view["preset_id"] = "unsafe"  # type: ignore[index]
    with pytest.raises(TypeError):
        view["feature_extraction"]["image_size_limit"] = 10  # type: ignore[index]

    source_digest = hashlib.sha256(b"source").hexdigest()
    from packlab_core.reconstruction import (
        ReconstructionBackendId,
        ReconstructionInputSet,
    )

    inputs = ReconstructionInputSet(
        "project",
        "raw/packscan.packscan",
        "revision-1",
        source_digest,
        ("working/images/001.jpg",),
    )
    job = ReconstructionJobSpec(
        "job-1",
        "project",
        1,
        inputs,
        ReconstructionBackendId.COLMAP_OPENMVS,
        configuration=view,
    )
    assert job.configuration["preset_identity"] == preset.preset_identity


@pytest.mark.parametrize(
    "overrides",
    [
        {"unknown": 1},
        {"--flag": "value"},
        {"SiftExtraction.max_num_features": 100},
        {"SequentialMatching.overlap": 2},
        {"Mapper.min_num_matches": 15},
        {"feature_extraction": {"SiftExtraction.max_num_features": 100}},
        {"matcher": {"SequentialMatching.overlap": 2}},
        {"sparse_mapping": {"Mapper.min_num_matches": 15}},
    ],
)
def test_unknown_and_engine_specific_fields_are_rejected(
    overrides: dict[str, object],
) -> None:
    with pytest.raises((ReconstructionPresetError, UnsupportedReconstructionPresetOption)):
        ReconstructionPreset.from_overrides(overrides)


@pytest.mark.parametrize(
    "overrides",
    [
        {"feature_extraction": {"image_size_limit": float("inf")}},
        {"feature_extraction": {"image_size_limit": "/private/images"}},
        {"sparse_mapping": {"image_path_asset_id": "C:/private/images"}},
        {"sparse_mapping": {"sparse_output_asset_id": "working/../private"}},
    ],
)
def test_invalid_values_and_private_paths_fail_closed(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        ReconstructionPreset.from_overrides(overrides)


@pytest.mark.parametrize("field", ["preset_id", "preset_version"])
def test_unsafe_preset_identity_is_rejected(field: str) -> None:
    with pytest.raises(ReconstructionPresetError):
        ReconstructionPreset.from_overrides({field: "../private"})


def test_nested_feature_alias_conflicts_fail_through_component_contract() -> None:
    with pytest.raises(ValueError, match="conflicting"):
        ReconstructionPreset.from_overrides(
            {
                "feature_extraction": {
                    "peak_threshold": 0.004,
                    "contrast_threshold": 0.005,
                }
            }
        )
