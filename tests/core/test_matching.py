from __future__ import annotations

import json

import pytest

from packlab_core.matching import (
    COLMAP_ENGINE_VERSION,
    CaptureMode,
    InvalidMatcherConfiguration,
    MatcherSelectionConfig,
    MatcherSelectionError,
    MatcherStrategy,
    TurntableMatcherUnsupported,
    UnsafeAssetId,
    UnsupportedCaptureMode,
    UnsupportedMatcherOption,
    map_to_colmap,
    select_matcher,
)


def _assets() -> list[str]:
    return ["raw/photos/frame-03.jpg", "raw/photos/frame-01.jpg", "raw/photos/frame-02.jpg"]


def test_guided_orbit_selects_sequential_strategy_and_preserves_exact_order() -> None:
    source = _assets()
    selection = select_matcher(
        source,
        CaptureMode.GUIDED_ORBIT,
        MatcherSelectionConfig(overlap=2, window_size=4),
    )

    assert selection.strategy is MatcherStrategy.SEQUENTIAL
    assert selection.image_asset_ids == tuple(source)
    assert selection.configuration.overlap == 2
    assert selection.configuration.window_size == 4
    assert source == _assets()


def test_selection_copies_mutable_input_and_does_not_mutate_configuration_mapping() -> None:
    source = _assets()
    overrides = {"overlap": 1, "window_size": 3}
    selection = select_matcher(source, "guided_orbit", overrides)

    source[0] = "raw/photos/changed.jpg"
    overrides["overlap"] = 3

    assert selection.image_asset_ids[0] == "raw/photos/frame-03.jpg"
    assert selection.configuration.overlap == 1
    assert selection.configuration.window_size == 3


@pytest.mark.parametrize(
    ("overlap", "window_size"),
    [(1, 2), (2, 3), (64, 65), (1, 256)],
)
def test_overlap_and_window_boundaries_are_accepted(overlap: int, window_size: int) -> None:
    config = MatcherSelectionConfig(overlap=overlap, window_size=window_size)
    selection = select_matcher(_assets(), "guided_orbit", config)

    assert selection.configuration.overlap == overlap
    assert selection.configuration.window_size == window_size


@pytest.mark.parametrize(
    ("overlap", "window_size"),
    [(0, 5), (65, 66), (2, 2), (3, 2), (1, 1), (1, 257)],
)
def test_invalid_overlap_and_window_values_fail_closed(overlap: int, window_size: int) -> None:
    with pytest.raises(InvalidMatcherConfiguration, match="overlap|window_size"):
        MatcherSelectionConfig(overlap=overlap, window_size=window_size)


@pytest.mark.parametrize("value", [True, 2.0, "2", None])
def test_non_integer_overlap_fails_closed(value: object) -> None:
    with pytest.raises(InvalidMatcherConfiguration, match="overlap"):
        MatcherSelectionConfig(overlap=value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "asset_ids",
    [
        [],
        ["only-one.jpg"],
        ["frame.jpg", "frame.jpg"],
        ["/private/frame.jpg", "frame-2.jpg"],
        ["C:/private/frame.jpg", "frame-2.jpg"],
        ["..\\frame.jpg", "frame-2.jpg"],
        ["raw/../frame.jpg", "frame-2.jpg"],
        ["raw//frame.jpg", "frame-2.jpg"],
        ["raw/./frame.jpg", "frame-2.jpg"],
        ["raw/frame\x00.jpg", "frame-2.jpg"],
    ],
)
def test_empty_duplicate_absolute_traversal_and_malformed_ids_fail_closed(
    asset_ids: list[str],
) -> None:
    with pytest.raises((MatcherSelectionError, UnsafeAssetId)):
        select_matcher(asset_ids, "guided_orbit")


def test_non_string_or_unordered_asset_input_is_rejected() -> None:
    with pytest.raises(MatcherSelectionError, match="ordered sequence"):
        select_matcher({"frame-1.jpg", "frame-2.jpg"}, "guided_orbit")  # type: ignore[arg-type]
    with pytest.raises(UnsafeAssetId, match="non-empty string"):
        select_matcher(["frame-1.jpg", 2], "guided_orbit")  # type: ignore[list-item]


@pytest.mark.parametrize("mode", ["guided-orbit", "freehand", "", 1])
def test_unsupported_capture_modes_fail_closed(mode: object) -> None:
    with pytest.raises(UnsupportedCaptureMode):
        select_matcher(_assets(), mode)  # type: ignore[arg-type]


def test_turntable_is_not_reinterpreted_as_static_world_guided_orbit() -> None:
    with pytest.raises(TurntableMatcherUnsupported, match="object-transform-aware"):
        select_matcher(_assets(), CaptureMode.TURNTABLE)


def test_configuration_serialization_and_digest_are_deterministic() -> None:
    first = select_matcher(_assets(), "guided_orbit", {"window_size": 6, "overlap": 3})
    second = select_matcher(tuple(_assets()), "guided_orbit", {"overlap": 3, "window_size": 6})

    assert first.configuration.serialize() == second.configuration.serialize()
    assert first.configuration.digest == second.configuration.digest
    assert first.serialize() == second.serialize()
    assert first.digest == second.digest
    assert len(first.digest) == 64
    assert json.loads(first.serialize())["contract"] == "packlab.matcher-selection.v1"


def test_selection_serialization_contains_only_valid_relative_provenance() -> None:
    selection = select_matcher(_assets(), "guided_orbit")
    serialized = selection.serialize()

    assert "C:/" not in serialized
    assert "\\\\" not in serialized
    assert ".." not in serialized
    assert json.loads(serialized)["ordered_image_asset_ids"] == _assets()


def test_unknown_configuration_and_strategy_fail_closed() -> None:
    with pytest.raises(UnsupportedMatcherOption, match="unsupported"):
        MatcherSelectionConfig.from_overrides({"quadratic": True})
    with pytest.raises(UnsupportedMatcherOption, match="sequential"):
        MatcherSelectionConfig.from_overrides({"strategy": "exhaustive"})


def test_colmap_adapter_is_explicit_configuration_only_and_version_checked() -> None:
    selection = select_matcher(_assets(), "guided_orbit", {"overlap": 3, "window_size": 5})
    mapped = map_to_colmap(selection)

    assert mapped == {
        "SequentialMatching.overlap": 3,
        "SequentialMatching.quadratic": False,
        "SequentialMatching.loop_detection": False,
    }
    with pytest.raises(UnsupportedMatcherOption, match=COLMAP_ENGINE_VERSION):
        map_to_colmap(selection, engine_version="3.13.0")
