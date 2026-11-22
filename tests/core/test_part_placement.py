"""PL-0484 closure-on-body placement on SYNTHETIC PROXY parts only (no real-accuracy claim).

Jar body (r 40 mm wall with a side boss fixing yaw, r 35 neck to 80 mm) and a round lid
(outer skirt r 37.5, inner skirt r 36, 15 mm tall, inner top 2 mm below the top) seated on the
neck: in the assembled scan the lid hides the neck. Each part is given in its own mat frame at
a random yaw / offset; the known placement is the ground truth.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("open3d")

from packlab_core.part_placement import (  # noqa: E402
    METRIC_STATUS,
    PartInput,
    PartPlacementError,
    place_closure_on_body,
    scan_assembly_graph,
)

SEAT = 67.0  # lid skirt bottom in the assembled frame (inner top 13 mm rests on the 80 mm neck)


def _cyl(rng, r, z0, z1, d=0.5):
    n = int(d * r * 2 * np.pi * (z1 - z0))
    a, z = rng.uniform(0, 2 * np.pi, n), rng.uniform(z0, z1, n)
    return np.c_[r * np.cos(a), r * np.sin(a), z]


def _disc(rng, r0, r1, z, d=0.5):
    n = int(d * np.pi * (r1**2 - r0**2))
    a, r = rng.uniform(0, 2 * np.pi, n), np.sqrt(rng.uniform(r0**2, r1**2, n))
    return np.c_[r * np.cos(a), r * np.sin(a), np.full(n, z)]


def _boss(rng, d=0.5):
    n = int(d * 20 * 30)
    return np.r_[
        np.c_[np.full(n, 44.0), rng.uniform(-10, 10, n), rng.uniform(15, 45, n)],
        np.c_[rng.uniform(38.7, 44, n // 4), np.full(n // 4, -10.0), rng.uniform(15, 45, n // 4)],
        np.c_[rng.uniform(38.7, 44, n // 4), np.full(n // 4, 10.0), rng.uniform(15, 45, n // 4)],
    ]


def body(rng, neck_top=80.0):
    return np.concatenate(
        [
            _cyl(rng, 40, 0, 65),
            _boss(rng),
            _disc(rng, 0, 40, 0),
            _disc(rng, 35, 40, 65),
            _cyl(rng, 35, 65, neck_top),
            _disc(rng, 0, 35, neck_top),
        ]
    )


def lid(rng, radius=37.5, height=15.0):
    """Combined lid (upright + flipped): outside, top, rim and the inside seen upside down."""
    inner = radius - 1.5
    return np.concatenate(
        [
            _cyl(rng, radius, 0, height),
            _disc(rng, 0, radius, height),
            _disc(rng, inner, radius, 0),
            _cyl(rng, inner, 0, height - 2),
            _disc(rng, 0, inner, height - 2),
        ]
    )


def assembled(rng):
    """Upright assembled scan: body below the lid (neck hidden), lid on top; no underside."""
    seen = np.concatenate(
        [_cyl(rng, 40, 0, 65), _boss(rng), _disc(rng, 37.5, 40, 65), _cyl(rng, 35, 65, SEAT)]
    )
    on = lid(rng)
    on = on[(np.linalg.norm(on[:, :2], axis=1) > 37.0) | (on[:, 2] > 14.0)] + [0, 0, SEAT]
    return np.r_[seen, on]


def _pose(yaw, x, y):
    c, s = np.cos(yaw), np.sin(yaw)
    m = np.eye(4)
    m[:3, :3] = [[c, -s, 0], [s, c, 0], [0, 0, 1]]
    m[:3, 3] = [x, y, 0]
    return m


def _move(m, points, rng):
    out = points @ m[:3, :3].T + m[:3, 3]
    return out + rng.normal(0, 0.15, out.shape)


def _inputs(seed, lid_radius=37.5, lid_height=15.0, upside_down=False, neck_top=80.0):
    rng = np.random.default_rng(seed)
    truth_b = _pose(rng.uniform(0, 2 * np.pi), *rng.uniform(-30, 30, 2))
    truth_c = _pose(rng.uniform(0, 2 * np.pi), *rng.uniform(-30, 30, 2))
    a = PartInput("assembled", _move(np.eye(4), assembled(rng), rng))
    b = PartInput("body", _move(np.linalg.inv(truth_b), body(rng, neck_top), rng))
    closure = lid(rng, lid_radius, lid_height)
    if upside_down:
        closure = closure * [1, -1, -1] + [0, 0, lid_height]
    c = PartInput("closure", _move(np.linalg.inv(truth_c), closure, rng))
    return a, b, c, truth_b, truth_c


@pytest.mark.parametrize("seed", [1, 2])
def test_known_placement_recovered_with_lid_occluding_body_top(seed) -> None:
    a, b, c, truth_b, truth_c = _inputs(seed)
    result = place_closure_on_body(a, b, c)
    assert result.metric_status == METRIC_STATUS
    # Body: boss fixes yaw -> full pose known.
    probe = body(np.random.default_rng(99))
    placed = probe @ result.body.matrix[:3, :3].T + result.body.matrix[:3, 3]
    error = np.linalg.norm(placed - (probe @ truth_b[:3, :3].T + truth_b[:3, 3]), axis=1)
    assert result.body.yaw_determined and error.max() < 1.5, error.max()
    # Lid: round, yaw arbitrary -> axis and height known.
    axis = np.array([[0.0, 0.0, 15.0], [0.0, 0.0, 0.0]])
    top = axis @ np.linalg.inv(truth_c)[:3, :3].T + np.linalg.inv(truth_c)[:3, 3]
    moved = top @ result.closure.matrix[:3, :3].T + result.closure.matrix[:3, 3]
    assert not result.closure.yaw_determined
    assert np.abs(moved - [[0, 0, SEAT + 15], [0, 0, SEAT]]).max() < 0.8, moved
    assert result.engaged_depth_mm == pytest.approx(13.0, abs=1.0)
    assert result.clearance.status in ("CLEARANCE", "NEAR_CLEARANCE")
    assert result.interference_point_share < 0.01 and result.interference_depth_mm < 1.0
    assert result.observed_seat_mm == pytest.approx(SEAT, abs=1.5)
    assert result.clearance.overlap_depth_estimate is None
    assert result.body.coverage > 0.9 and result.closure.coverage > 0.9


def test_deterministic_and_graph_revision_stable() -> None:
    a, b, c, *_ = _inputs(3)
    first, second = place_closure_on_body(a, b, c), place_closure_on_body(a, b, c)
    assert np.array_equal(first.closure.matrix, second.closure.matrix)
    sources = {k: {"cloud": f"{k}.ply"} for k in ("assembled", "body", "closure")}
    graph = scan_assembly_graph(first, sources, "test")
    assert graph == scan_assembly_graph(second, sources, "test")
    assert graph["revision_id"].startswith("scan-assembly-graph:")
    assert [c["role"] for c in graph["components"]] == ["container", "closure"]
    assert graph["components"][0]["placement"]["transform_convention"]
    assert graph["mold_use_authorized"] is False and graph["metric_status"] == METRIC_STATUS


def test_wrong_lid_diameter_refused() -> None:
    a, b, c, *_ = _inputs(4, lid_radius=43.0)
    with pytest.raises(PartPlacementError) as caught:
        place_closure_on_body(a, b, c)
    assert caught.value.codes and set(caught.value.codes) & {"diameter_mismatch", "coverage"}


def test_floating_and_missing_parts_refused() -> None:
    a, b, c, *_ = _inputs(5)
    with pytest.raises(PartPlacementError) as caught:
        place_closure_on_body(a, None, c)
    assert caught.value.codes == ("part_missing",) and "body" in str(caught.value)
    short = PartInput("short", b.points[b.points[:, 2] < 60.0])  # lid would float 7 mm
    with pytest.raises(PartPlacementError) as caught:
        place_closure_on_body(a, short, c)
    assert "height_inconsistent" in caught.value.codes
    with pytest.raises(PartPlacementError) as caught:
        place_closure_on_body(a, PartInput("tiny", b.points[:20]), c)
    assert caught.value.codes == ("part_unusable",)


@pytest.mark.parametrize("seed", [21, 22])
def test_short_lid_of_same_diameter_refused_by_seat_check(seed) -> None:
    a, b, c, *_ = _inputs(seed, lid_height=12.0)  # placed 3 mm too high without the seat check
    with pytest.raises(PartPlacementError) as caught:
        place_closure_on_body(a, b, c)
    assert "seat_mismatch" in caught.value.codes and "rescan" in str(caught.value)


@pytest.mark.parametrize(
    ("case", "kwargs"),
    [("upside-down lid", {"upside_down": True}), ("tall neck", {"neck_top": 82.5})],
)
def test_gross_interference_refused(case, kwargs) -> None:
    a, b, c, *_ = _inputs(21, **kwargs)
    with pytest.raises(PartPlacementError) as caught:
        place_closure_on_body(a, b, c)
    assert set(caught.value.codes) & {"interference", "seat_mismatch", "free_space_conflict"}, case


def test_part_from_scan_keeps_colours() -> None:
    from packlab_core.multiscan_alignment import ScanInput
    from packlab_core.part_placement import part_from_scan

    rng = np.random.default_rng(31)
    mat = np.c_[rng.uniform(-148, 148, 18000), rng.uniform(-105, 105, 18000), np.zeros(18000)]
    points = np.r_[body(rng), mat] + rng.normal(0, 0.15, (1, 3))
    colours = np.where(points[:, 2:3] > 1.0, [[1.0, 0.0, 0.0]], [[0.0, 0.0, 1.0]])
    part = part_from_scan(ScanInput("b", points, colours))
    assert part.colors is not None and len(part.colors) == len(part.points)
    assert np.allclose(part.colors[part.points[:, 2] > 3.0], [1.0, 0.0, 0.0])
