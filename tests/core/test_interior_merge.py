"""PL-0489 body-interior merge on SYNTHETIC PROXY parts only (no real-accuracy claim).

Open jar body: outer wall r 40 mm, wall 2.5 mm (inner r 37.5), 100 mm tall, floor 3 mm thick.
The outer scan sees the outside, the rim and 5 mm into the opening; the interior scan (steep
rings) sees the rim, the top of the outer wall and the inner wall down to a known depth, given
in its own mat frame with a small known yaw / offset / tilt.
"""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("open3d")

from packlab_core.interior_merge import (  # noqa: E402
    METRIC_STATUS,
    InteriorMergeError,
    merge_interior,
    reachability,
)
from packlab_core.part_placement import PartInput  # noqa: E402

H, R, WALL = 100.0, 40.0, 2.5


def _cyl(rng, r, z0, z1, d=0.6):
    n = int(d * r * 2 * np.pi * (z1 - z0))
    a, z = rng.uniform(0, 2 * np.pi, n), rng.uniform(z0, z1, n)
    return np.c_[r * np.cos(a), r * np.sin(a), z]


def _disc(rng, r0, r1, z, d=0.6):
    n = int(d * np.pi * (r1**2 - r0**2))
    a, r = rng.uniform(0, 2 * np.pi, n), np.sqrt(rng.uniform(r0**2, r1**2, n))
    return np.c_[r * np.cos(a), r * np.sin(a), np.full(n, z)]


def outer_scan(rng, r=R, h=H):
    return np.concatenate(
        [_cyl(rng, r, 0, h), _disc(rng, r - WALL, r, h), _cyl(rng, r - WALL, h - 5, h)]
    )


def interior_scan(rng, depth, r=R, h=H, floor=False):
    parts = [_disc(rng, r - WALL, r, h), _cyl(rng, r, h - 10, h), _cyl(rng, r - WALL, h - depth, h)]
    if floor:
        parts.append(_disc(rng, 0, r - WALL, 3.0))
    return np.concatenate(parts)


def _moved(rng, points, yaw=0.5, shift=(4.0, -3.0), tilt=0.8):
    c, s = np.cos(yaw), np.sin(yaw)
    t = np.radians(tilt)
    rx = np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])
    rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    moved = points @ (rz @ rx).T + [*shift, 0]
    return moved + rng.normal(0, 0.15, moved.shape)


def _inputs(rng, depth, **kwargs):
    points = outer_scan(rng)
    body = PartInput("body", points + rng.normal(0, 0.15, points.shape))
    interior = PartInput("interior", _moved(rng, interior_scan(rng, depth, **kwargs)))
    return body, interior


def test_partial_depth_coverage_and_missing_bands() -> None:
    rng = np.random.default_rng(1)
    body, interior = _inputs(rng, 60.0)
    result = merge_interior(body, interior)
    assert result.metric_status == METRIC_STATUS == "METRIC_UNVERIFIED"
    assert result.reachability.reachable
    assert result.rim["body_diameter_mm"] == pytest.approx(2 * R - WALL, abs=1.5)
    assert result.deepest_covered_mm == pytest.approx(60.0, abs=2.5)
    assert result.yaw_determined is False  # round rim: yaw arbitrary, flagged
    # Bands from the rim to the scanned depth are covered, everything deeper is missing.
    covered = [b for b in result.bands if b.bottom_mm <= 58]
    assert covered and all(b.coverage >= 0.9 for b in covered)
    deeper = [b for b in result.bands if b.top_mm >= 62]
    assert deeper and all(b.coverage == 0 for b in deeper)
    assert result.missing[-1][1] == pytest.approx(H, abs=1.0)
    assert result.missing[0][0] == pytest.approx(60.0, abs=2.5)
    # Only interior points are added, from the interior scan, inside the wall; nothing filled.
    added = result.points[result.source_index == 1]
    assert len(added) and result.source_ids == ("body", "interior")
    radius = np.linalg.norm(added[:, :2], axis=1)
    assert np.percentile(np.abs(radius - (R - WALL)), 95) < 0.8  # aligned onto the inner wall
    assert added[:, 2].min() > H - 62
    assert len(result.points) == len(body.points) + len(added)
    rows = result.point_index[result.source_index == 1]
    assert np.allclose(result.points[result.source_index == 1], added)
    assert rows.max() < len(interior.points)


def test_full_depth_with_floor_reaches_the_floor() -> None:
    rng = np.random.default_rng(2)
    body, interior = _inputs(rng, H - 3, floor=True)
    result = merge_interior(body, interior)
    assert result.deepest_covered_mm >= H - 4  # the floor at 3 mm closes the last bands
    assert all(top >= H - 4 for top, _ in result.missing)


@pytest.mark.parametrize(
    ("kwargs", "detail"), [({"r": 45.0}, "diameter"), ({"h": 110.0}, "height")]
)
def test_rim_mismatch_refused(kwargs, detail) -> None:
    rng = np.random.default_rng(3)
    body, interior = _inputs(rng, 50.0, **kwargs)
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, interior)
    assert error.value.codes == ("rim_mismatch",) and detail in str(error.value)


def test_no_rim_refused() -> None:
    rng = np.random.default_rng(4)
    body = PartInput("body", outer_scan(rng))
    half = interior_scan(rng, 50.0)
    half = half[half[:, 0] > 10]  # one side of the opening only
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", half))
    assert error.value.codes == ("rim_not_found",)


def test_nothing_below_the_rim_is_insufficient_overlap() -> None:
    rng = np.random.default_rng(5)
    body = PartInput("body", outer_scan(rng))
    only_rim = np.r_[_disc(rng, R - WALL, R, H), _cyl(rng, R, H - 10, H)]
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", _moved(rng, only_rim)))
    assert error.value.codes == ("insufficient_overlap",)


def test_narrow_neck_bottle_not_reachable() -> None:
    rng = np.random.default_rng(6)
    bottle = np.concatenate(
        [
            _cyl(rng, 35, 0, 150),
            _disc(rng, 11, 35, 160),
            _cyl(rng, 11, 160, 180),
            _disc(rng, 9.5, 11, 180, d=4.0),
        ]
    )
    reach = reachability(PartInput("bottle", bottle))
    assert not reach.reachable and "PL-0488" in reach.reason
    assert reach.opening_mm < 25 and reach.reachable_depth_mm < 180
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(PartInput("bottle", bottle), PartInput("interior", bottle))
    assert error.value.codes == ("interior_not_reachable",)
