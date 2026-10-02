from __future__ import annotations

import math

import pytest

from packlab_core.front_direction import (
    FrontDirectionError,
    append_front_direction_revision,
    select_front_direction,
    serialize_front_direction,
)

PARENTS = {
    "base_plane_selection_id": "plane-r1",
    "upright_alignment_id": "upright-r1",
    "geometry_id": "geometry-r1",
    "reconstruction_revision": "reconstruction-r1",
    "camera_solution_revision": "camera-r1",
}


def _select(direction=(3.0, 4.0, 0.0)):
    return select_front_direction(
        direction,
        source="operator_selection",
        actor_id="operator-1",
        evidence_id="selection-event-1",
        **PARENTS,
        coordinate_unit="reconstruction_units",
    )


@pytest.mark.parametrize("direction", [(1, 0, 0), (0, -1, 0), (1, 2, 0)])
def test_cardinal_and_arbitrary_horizontal_front_is_normalized(direction) -> None:
    result = _select(direction)
    assert math.isclose(math.hypot(result.direction[0], result.direction[1]), 1.0)
    assert result.direction[2] == 0.0


@pytest.mark.parametrize("direction", [(0, 0, 1), (0, 0, 0), (1, 2, math.nan), (1, 2, math.inf)])
def test_vertical_zero_and_non_finite_front_are_rejected(direction) -> None:
    with pytest.raises(FrontDirectionError):
        _select(direction)


def test_operator_provenance_and_serialized_metadata_are_deterministic() -> None:
    first = _select()
    repeated = _select()
    assert first.source == "operator_selection"
    assert first.actor_id == "operator-1"
    assert first.evidence_id == "selection-event-1"
    assert first.revision_id == repeated.revision_id
    assert serialize_front_direction(first) == serialize_front_direction(repeated)
    assert first.as_dict()["physical_front_verified"] is False


def test_front_history_is_append_only_and_rejects_stale_parent() -> None:
    first = _select((1, 0, 0))
    history = append_front_direction_revision([], first, current_parent_ids=dict(PARENTS))
    second = select_front_direction(
        (0, 1, 0),
        source="operator_selection",
        actor_id="operator-1",
        evidence_id="event-2",
        **PARENTS,
        coordinate_unit="reconstruction_units",
    )
    extended = append_front_direction_revision(history, second, current_parent_ids=dict(PARENTS))
    assert len(history) == 1
    assert len(extended) == 2
    assert extended[0] == history[0]
    stale = dict(PARENTS, reconstruction_revision="reconstruction-r2")
    with pytest.raises(FrontDirectionError, match="stale_parent"):
        append_front_direction_revision(extended, first, current_parent_ids=stale)
