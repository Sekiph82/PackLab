from __future__ import annotations

import json
import math

import pytest

from packlab_core.feature_extraction import (
    COLMAP_ENGINE_VERSION,
    PACKAGED_CONSUMER_GOODS_PRESET,
    FeatureExtractionConfig,
    FeatureExtractionConfigError,
    OrientationPolicy,
    UnsupportedFeatureExtractionOption,
    map_to_colmap,
    unsupported_colmap_options,
)


def test_packaged_goods_preset_has_named_defaults_and_limitations() -> None:
    config = PACKAGED_CONSUMER_GOODS_PRESET

    assert config.preset_identity == "packaged-consumer-goods-v1:1"
    assert config.image_size_limit == 4096
    assert config.feature_count_limit == 12_000
    assert config.first_octave == -1
    assert config.octave_count == 4
    assert config.octave_resolution == 3
    assert config.contrast_peak_threshold == 0.004
    assert config.edge_threshold == 10.0
    assert config.orientation_policy is OrientationPolicy.ROTATION_INVARIANT
    assert any("larger image" in note for note in config.tradeoff_notes)
    assert any("not physically benchmarked" in note for note in config.limitations)


def test_valid_overrides_are_immutable_and_support_generic_threshold_alias() -> None:
    source = {"feature_count_limit": 16_000, "contrast_threshold": 0.006}
    original = dict(source)
    updated = FeatureExtractionConfig.from_overrides(source)

    assert source == original
    assert PACKAGED_CONSUMER_GOODS_PRESET.feature_count_limit == 12_000
    assert updated.feature_count_limit == 16_000
    assert updated.contrast_peak_threshold == 0.006
    assert updated.preset_identity == PACKAGED_CONSUMER_GOODS_PRESET.preset_identity


def test_serialization_and_digest_are_order_independent() -> None:
    first = FeatureExtractionConfig.from_overrides(
        {"edge_threshold": 8.0, "feature_count_limit": 14_000}
    )
    second = FeatureExtractionConfig.from_overrides(
        {"feature_count_limit": 14_000, "edge_threshold": 8.0}
    )

    assert first.serialize() == second.serialize()
    assert first.configuration_digest() == second.configuration_digest()
    assert len(first.digest) == 64
    assert json.loads(first.serialize())["contract"] == "packlab.feature-extraction.v1"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("image_size_limit", 255),
        ("feature_count_limit", 100_001),
        ("first_octave", -3),
        ("octave_count", 0),
        ("octave_resolution", 9),
        ("contrast_peak_threshold", 0.00009),
        ("edge_threshold", 100.1),
        ("orientation_policy", "sideways"),
    ],
)
def test_invalid_ranges_and_unsupported_orientation_are_rejected(field: str, value: object) -> None:
    with pytest.raises(FeatureExtractionConfigError):
        FeatureExtractionConfig.from_overrides({field: value})


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_thresholds_are_rejected(value: float) -> None:
    with pytest.raises(FeatureExtractionConfigError):
        FeatureExtractionConfig.from_overrides({"contrast_peak_threshold": value})


def test_unknown_backend_options_and_absolute_paths_fail_closed() -> None:
    with pytest.raises(UnsupportedFeatureExtractionOption):
        FeatureExtractionConfig.from_overrides({"use_gpu": True})
    with pytest.raises(UnsupportedFeatureExtractionOption):
        FeatureExtractionConfig.from_overrides({"mask_path": "C:/private/capture"})
    with pytest.raises(FeatureExtractionConfigError, match="absolute paths"):
        FeatureExtractionConfig.from_overrides({"feature_count_limit": "/tmp/16000"})
    with pytest.raises(FeatureExtractionConfigError):
        FeatureExtractionConfig.from_overrides({"future_option": 1})
    with pytest.raises(FeatureExtractionConfigError, match="absolute paths"):
        FeatureExtractionConfig(limitations=("C:/private/capture",))
    assert "use_gpu" in unsupported_colmap_options()


def test_colmap_adapter_mapping_is_explicit_and_does_not_execute_engine() -> None:
    config = FeatureExtractionConfig.from_overrides(
        {"orientation_policy": OrientationPolicy.UPRIGHT, "first_octave": 0}
    )
    mapped = map_to_colmap(config)

    assert mapped == {
        "SiftExtraction.max_image_size": 4096,
        "SiftExtraction.max_num_features": 12_000,
        "SiftExtraction.first_octave": 0,
        "SiftExtraction.num_octaves": 4,
        "SiftExtraction.octave_resolution": 3,
        "SiftExtraction.peak_threshold": 0.004,
        "SiftExtraction.edge_threshold": 10.0,
        "SiftExtraction.upright": True,
    }
    with pytest.raises(UnsupportedFeatureExtractionOption):
        map_to_colmap(config, engine_version="3.13.0")
    assert COLMAP_ENGINE_VERSION == "3.12.6"
