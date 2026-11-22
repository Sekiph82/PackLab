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


def outer_scan(rng, r=R, h=H, wall=WALL):
    return np.concatenate(
        [_cyl(rng, r, 0, h), _disc(rng, r - wall, r, h, d=2.0), _cyl(rng, r - wall, h - 5, h)]
    )


def interior_scan(rng, depth, r=R, h=H, floor=False, wall=WALL, outer_from=None):
    """Rim, outer wall from ``outer_from`` (default h - 10) up, inner wall down to ``depth``."""
    outer_from = h - 10 if outer_from is None else outer_from
    parts = [
        _disc(rng, r - wall, r, h, d=2.0),
        _cyl(rng, r, outer_from, h),
        _cyl(rng, r - wall, h - depth, h),
    ]
    if floor:
        parts.append(_disc(rng, 0, r - wall, 3.0))
    return np.concatenate(parts)


def _moved(rng, points, yaw=0.5, shift=(4.0, -3.0), tilt=0.1):
    """Own mat frame: yaw / offset free, tilt only a residual of the mat levelling."""
    c, s = np.cos(yaw), np.sin(yaw)
    t = np.radians(tilt)
    rx = np.array([[1, 0, 0], [0, np.cos(t), -np.sin(t)], [0, np.sin(t), np.cos(t)]])
    rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    moved = points @ (rz @ rx).T + [*shift, 0]
    return moved + rng.normal(0, 0.15, moved.shape)


def _inputs(rng, depth, wall=WALL, **kwargs):
    points = outer_scan(rng, wall=wall)
    body = PartInput("body", points + rng.normal(0, 0.15, points.shape))
    interior = PartInput("interior", _moved(rng, interior_scan(rng, depth, wall=wall, **kwargs)))
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


@pytest.mark.parametrize("wall", [2.5, 1.5, 1.0, 0.5])
def test_thin_walls_keep_the_scanned_depth(wall) -> None:
    """HDPE/PET walls: the outer wall seen down to the mat must not hide the inner wall."""
    rng = np.random.default_rng(int(wall * 10))
    body, interior = _inputs(rng, 60.0, wall=wall, outer_from=0.0)
    result = merge_interior(body, interior)
    assert result.wall_mm == pytest.approx(wall, abs=0.3)
    assert result.deepest_covered_mm == pytest.approx(60.0, abs=2.5)
    added = result.points[result.source_index == 1]
    radius = np.linalg.norm(added[:, :2], axis=1)
    assert np.mean(radius > R - wall / 2) < 0.1  # few outer-wall points taken as interior


def test_floaters_are_not_interior_and_sparse_sectors_do_not_count() -> None:
    rng = np.random.default_rng(31)
    body, interior = _inputs(rng, 30.0)
    # isolated floaters inside the jar below the scanned depth, one per sector and band
    angle = np.linspace(0, 2 * np.pi, 36, endpoint=False)
    floaters = np.concatenate(
        [np.c_[30 * np.cos(angle), 30 * np.sin(angle), np.full(36, z)] for z in (20.0, 40.0)]
    )
    points = np.r_[interior.points, _moved(rng, floaters)]
    result = merge_interior(body, PartInput("interior", points))
    rows = result.point_index[result.source_index == 1]
    assert rows.max() < len(interior.points)  # no floater written as interior
    assert result.deepest_covered_mm == pytest.approx(30.0, abs=2.5)


def test_height_offset_near_tolerance_keeps_coverage() -> None:
    rng = np.random.default_rng(32)
    body, interior = _inputs(rng, 60.0)
    lifted = PartInput("interior", interior.points + [0, 0, 1.4])
    result = merge_interior(body, lifted)
    assert result.rim["height_offset_mm"] == pytest.approx(-1.4, abs=0.4)
    assert result.deepest_covered_mm == pytest.approx(60.0, abs=2.5)
    assert all(b.coverage >= 0.9 for b in result.bands if b.bottom_mm <= 58)


def test_base_under_the_floor_is_not_reported_missing() -> None:
    rng = np.random.default_rng(33)
    body, interior = _inputs(rng, H - 3, floor=True)
    result = merge_interior(body, interior)
    assert result.floor_depth_mm == pytest.approx(H - 3, abs=0.5)
    assert result.deepest_covered_mm == pytest.approx(H - 3, abs=0.5)
    assert result.interior_provenance == "SCANNED_TO_FLOOR"
    assert result.missing == ()
    assert [b.kind for b in result.bands][-1] == "base"


def test_different_jar_interior_refused() -> None:
    """Same rim, but the interior narrows to a 30 mm radius well inside a 40 mm body."""
    rng = np.random.default_rng(34)
    body = PartInput("body", outer_scan(rng))
    other = np.r_[
        _disc(rng, R - WALL, R, H, d=2.0),
        _cyl(rng, R, H - 10, H),
        _cyl(rng, R - WALL, H - 20, H),
        _cyl(rng, 30.0, H - 80, H - 20),
    ]
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", _moved(rng, other)))
    assert error.value.codes[0] in ("interior_wall_implausible", "interior_profile_mismatch")


def _foreign(rng, inner):
    """Interior scan with the body's rim and outer wall top, but ``inner`` as its inside."""
    return np.r_[_disc(rng, R - WALL, R, H, d=2.0), _cyl(rng, R, H - 10, H), inner]


@pytest.mark.parametrize(
    "case",
    ["outside_r42", "inset_6mm", "taper"],
)
def test_impossible_or_foreign_interior_refused(case) -> None:
    rng = np.random.default_rng(41)
    body = PartInput("body", outer_scan(rng))
    if case == "outside_r42":  # inner wall outside the body's outer wall
        inner = _cyl(rng, 42.0, H - 60, H - 3)
    elif case == "inset_6mm":
        inner = _cyl(rng, R - 6.0, H - 60, H - 3)
    else:  # foreign jar narrowing from r 37.5 to r 28 with depth
        z = rng.uniform(H - 70, H - 3, 12000)
        a = rng.uniform(0, 2 * np.pi, len(z))
        r = 28.0 + (R - WALL - 28.0) * (z - (H - 70)) / 67.0
        inner = np.c_[r * np.cos(a), r * np.sin(a), z]
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", _moved(rng, _foreign(rng, inner))))
    assert error.value.codes[0] in ("interior_wall_implausible", "interior_profile_mismatch")


def test_reflection_blob_inside_the_cavity_is_not_written() -> None:
    rng = np.random.default_rng(42)
    body, interior = _inputs(rng, 60.0)
    blob = rng.normal(0, 2.0, (1500, 3)) + [10.0, 0.0, 70.0]  # dense, away from the wall
    points = np.r_[interior.points, _moved(rng, blob)]
    result = merge_interior(body, PartInput("interior", points))
    rows = result.point_index[result.source_index == 1]
    assert (rows >= len(interior.points)).sum() == 0
    assert result.deepest_covered_mm == pytest.approx(60.0, abs=2.5)


def test_mostly_floaters_is_too_noisy() -> None:
    rng = np.random.default_rng(43)
    body, interior = _inputs(rng, 60.0)
    z = rng.uniform(10, 95, 3000)
    a, r = rng.uniform(0, 2 * np.pi, 3000), rng.uniform(0, 36, 3000)
    floaters = np.c_[r * np.cos(a), r * np.sin(a), z]
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", np.r_[interior.points, _moved(rng, floaters)]))
    assert error.value.codes == ("too_noisy",)


@pytest.mark.parametrize("seed", [20, 21, 22])
def test_real_wall_then_outside_the_body_refused(seed) -> None:
    """10 mm of a real 1.5 mm wall, then walls at r 42 outside the r 40 body: never merged."""
    rng = np.random.default_rng(seed)
    points = outer_scan(rng, wall=1.5)
    body = PartInput("body", points + rng.normal(0, 0.15, points.shape))
    mixed = np.r_[
        _disc(rng, R - 1.5, R, H, d=2.0),
        _cyl(rng, R, H - 10, H),
        _cyl(rng, R - 1.5, H - 10, H),
        _cyl(rng, 42.0, 20, H - 10),
    ]
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", _moved(rng, mixed)))
    assert error.value.codes == ("interior_wall_implausible",)


def test_thick_wall_scales_with_the_rim_radius() -> None:
    """r 80 jar with a 6 mm wall merges (bound 8 mm); the same wall on r 40 is refused."""
    rng = np.random.default_rng(44)
    big = 80.0
    points = outer_scan(rng, r=big, wall=6.0)
    body = PartInput("body", points + rng.normal(0, 0.15, points.shape))
    interior = PartInput("interior", _moved(rng, interior_scan(rng, 60.0, r=big, wall=6.0)))
    result = merge_interior(body, interior)
    assert result.wall_mm == pytest.approx(6.0, abs=0.4)
    assert result.deepest_covered_mm == pytest.approx(60.0, abs=2.5)


def test_rim_only_with_floaters_is_too_noisy() -> None:
    rng = np.random.default_rng(45)
    body = PartInput("body", outer_scan(rng))
    xy = rng.uniform(-30, 30, (3000, 2))
    floaters = np.c_[xy, rng.uniform(5, 90, 3000)][np.linalg.norm(xy, axis=1) < 34]
    rim = np.r_[_disc(rng, R - WALL, R, H, d=2.0), _cyl(rng, R, H - 10, H), floaters]
    with pytest.raises(InteriorMergeError) as error:
        merge_interior(body, PartInput("interior", _moved(rng, rim)))
    assert error.value.codes == ("too_noisy",)
