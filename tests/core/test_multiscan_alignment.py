"""PL-0483 multi-scan alignment on SYNTHETIC PROXY shapes only (no real-accuracy claim).

Shapes have known metric ground truth (mm); each scan = visible faces + A4 mat plane + noise,
placed on the mat at a random yaw/offset and seen through a random similarity (camera units).
"""

from __future__ import annotations

from dataclasses import replace

import numpy as np
import pytest

pytest.importorskip("open3d")

from packlab_core.multiscan_alignment import (  # noqa: E402
    METRIC_STATUS,
    AlignmentThresholds,
    MultiScanAlignmentError,
    ScanInput,
    align_part_pair,
    align_scans,
    check_alignment,
)
from packlab_core.multiscan_alignment import _prepare as prepare_scan  # noqa: E402


class _Gen:
    """Seeded sampler carrying the surface point density (points per mm^2)."""

    def __init__(self, rng, density):
        self.rng, self.density = rng, density

    def uniform(self, *args):
        return self.rng.uniform(*args)


def _cyl(rng, r, z0, z1, a0=0.0, a1=2 * np.pi):
    n = int(rng.density * r * (a1 - a0) * (z1 - z0))
    a, z = rng.uniform(a0, a1, n), rng.uniform(z0, z1, n)
    return np.c_[r * np.cos(a), r * np.sin(a), z]


def _disc(rng, r0, r1, z):
    n = int(rng.density * np.pi * (r1**2 - r0**2))
    a, r = rng.uniform(0, 2 * np.pi, n), np.sqrt(rng.uniform(r0**2, r1**2, n))
    return np.c_[r * np.cos(a), r * np.sin(a), np.full(n, z)]


def _rect(rng, x, y0, y1, z0, z1):  # plane x = const
    n = int(rng.density * (y1 - y0) * (z1 - z0))
    return np.c_[np.full(n, x), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)]


def _wall(rng, y, x0, x1, z0, z1):  # plane y = const
    return _rect(rng, 0, x0, x1, z0, z1)[:, [1, 0, 2]] + [0, y, 0]


def _cap(rng, x0, x1, y0, y1, z):  # plane z = const
    n = int(rng.density * (x1 - x0) * (y1 - y0))
    return np.c_[rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), np.full(n, z)]


def body(rng, r=40.0, h=80.0, boss=True):
    """Jar body proxy: r 40, h 80, off-centre 20x30x4 mm side boss (fixes yaw and flip)."""
    faces = {
        "side": _cyl(rng, r, 0, h),
        "top": _disc(rng, 0, r, h),
        "bottom": _disc(rng, 0, r, 0),
    }
    if boss:
        faces["boss"] = np.r_[
            _rect(rng, r + 4, -10, 10, 15, 45),
            _wall(rng, -10, r - 1.3, r + 4, 15, 45),
            _wall(rng, 10, r - 1.3, r + 4, 15, 45),
            _cap(rng, r - 1, r + 4, -10, 10, 15),
            _cap(rng, r - 1, r + 4, -10, 10, 45),
        ]
    return h, faces


def closure(rng):
    """Lid proxy: r 45, h 15 disc, 10 mm deep r 40 recess underneath, 7 mm side tab."""
    return 15.0, {
        "side": _cyl(rng, 45, 0, 15),
        "boss": np.r_[
            _rect(rng, 52, -6, 6, 0, 15),
            _wall(rng, -6, 44.6, 52, 0, 15),
            _wall(rng, 6, 44.6, 52, 0, 15),
        ],
        "top": np.r_[_disc(rng, 0, 45, 15), _cap(rng, 44, 52, -6, 6, 15)],
        "bottom": np.r_[
            _disc(rng, 40, 45, 0),
            _disc(rng, 0, 40, 10),
            _cyl(rng, 40, 0, 10),
            _cap(rng, 44, 52, -6, 6, 0),
        ],
    }


def cylinder(rng):
    """Rotationally symmetric body proxy (no boss): yaw is unobservable."""
    return body(rng, boss=False)


def _rot(axis, angle):
    axis = np.asarray(axis, float) / np.linalg.norm(axis)
    k = np.array([[0, -axis[2], axis[1]], [axis[2], 0, -axis[0]], [-axis[1], axis[0], 0]])
    return np.eye(3) + np.sin(angle) * k + (1 - np.cos(angle)) * k @ k


def _hom(rotation, translation, scale=1.0):
    m = np.eye(4)
    m[:3, :3], m[:3, 3] = scale * rotation, translation
    return m


def _apply(m, p):
    return p @ m[:3, :3].T + m[:3, 3]


def scan(
    shape,
    flipped,
    seed,
    *,
    keep_frac=1.0,
    floaters=0,
    subsample=1.0,
    tilt_deg=None,
    scale_error=1.0,
    role="given",
    density=0.5,
    clutter=False,
    wall_gap=False,
    paint=None,
    halo=False,
    cut_top=0.0,
    **shape_args,
):
    """Return (ScanInput, object->camera-units 4x4) for an upright or upside-down capture.

    tilt_deg: pass ``to_mat_mm`` from the true mat pose with that tilt error added.
    scale_error: multiplies the mm_per_unit handed to the aligner.
    paint: object-frame points -> RGB (a printed label); default one flat tone everywhere.
    halo: white specular glare MVS lifted 1.6-4 mm off the mat in a ring around the foot.
    cut_top: mm of the part's top (mat frame) the MVS missed in this scan.
    """
    rng = np.random.default_rng(seed)
    height, faces = shape(_Gen(rng, density), **shape_args)
    hidden = "top" if flipped else "bottom"  # face on the mat is not seen
    obj = np.concatenate([p for name, p in faces.items() if name != hidden])
    if wall_gap:  # glossy band of the part the MVS missed: splits the wall into two clusters
        obj = obj[(obj[:, 2] < 50) | (obj[:, 2] > 60)]
    if keep_frac < 1.0:  # only the part of the object nearest the camera (top in mat frame)
        z_mat = height - obj[:, 2] if flipped else obj[:, 2]
        obj = obj[z_mat > (1 - keep_frac) * height]
    if cut_top:
        z_mat = height - obj[:, 2] if flipped else obj[:, 2]
        obj = obj[z_mat < height - cut_top]
    place = _hom(_rot([0, 0, 1], rng.uniform(0, 2 * np.pi)), [*rng.uniform(-30, 30, 2), 0])
    if flipped:
        place = place @ _hom(_rot([1, 0, 0], np.pi), [0, 0, height])
    count = int(18000 * density / 0.5)
    mat = np.c_[rng.uniform(-148, 148, count), rng.uniform(-105, 105, count), np.zeros(count)]
    pts = np.r_[_apply(place, obj), mat] + rng.normal(0, 0.15, (len(obj) + count, 3))
    tone = np.array([0.2, 0.4, 0.6])
    colors = np.r_[paint(obj) if paint else np.tile(tone, (len(obj), 1)), np.tile(tone, (count, 1))]
    if halo:
        foot = np.max(np.linalg.norm(obj[:, :2], axis=1))
        n = int(2000 * density / 0.5)
        a, r = rng.uniform(0, 2 * np.pi, n), rng.uniform(foot + 1, foot + 30, n)
        ring = np.c_[r * np.cos(a), r * np.sin(a), rng.uniform(1.6, 4.0, n)] + place[:3, 3] * [
            1,
            1,
            0,
        ]
        pts, colors = np.r_[pts, ring], np.r_[colors, np.full((n, 3), 0.9)]
    if clutter:  # a bigger box standing on the table beside (not on) the A4 mat
        box = rng.uniform([170, -60, 0], [260, 60, 60], (int(20000 * density), 3))
        pts, colors = np.r_[pts, box], np.r_[colors, np.tile(tone, (len(box), 1))]
    if floaters:  # MVS-like stray points floating above the part
        stray = rng.uniform([-60, -60, height + 5], [60, 60, height + 60], (floaters, 3))
        pts, colors = np.r_[pts, stray], np.r_[colors, np.tile(tone, (floaters, 1))]
    if subsample < 1.0:
        keep = rng.random(len(pts)) < subsample
        pts, colors = pts[keep], colors[keep]
    scale = rng.uniform(0.01, 0.05)  # camera units per mm
    camera = _hom(_rot(rng.normal(size=3), rng.uniform(0, np.pi)), rng.normal(size=3), scale)
    sid = f"{shape.__name__}-{'flipped' if flipped else 'upright'}-{seed}"
    to_mat = None
    if tilt_deg is not None:
        to_mat = _hom(_rot([1, 1, 0], np.radians(tilt_deg)), np.zeros(3)) @ np.linalg.inv(camera)
    scan_input = ScanInput(
        sid,
        _apply(camera, pts),
        colors,
        to_mat_mm=to_mat,
        mm_per_unit=scale_error / scale,
        flipped={"given": flipped, "unknown": None, "wrong": not flipped}[role],
    )
    return scan_input, camera @ place


def _pose_error(result, truths, index=1):
    e = result.alignments[0].matrix @ truths[0]
    g = result.alignments[index].matrix @ truths[index]
    d = np.linalg.inv(e) @ g
    d[:3, :3] /= np.cbrt(np.linalg.det(d[:3, :3]))
    angle = np.degrees(np.arccos(np.clip((np.trace(d[:3, :3]) - 1) / 2, -1, 1)))
    return angle, float(np.linalg.norm(d[:3, 3]))


def _assert_recovered(result, truths, index=1):
    angle, shift = _pose_error(result, truths, index)
    assert angle < 1.0 and shift < 0.5, (angle, shift)


@pytest.mark.parametrize("shape", [body, closure])
def test_upright_and_flipped_pair_recovers_known_transform(shape):
    (up, t_up), (fl, t_fl) = scan(shape, False, 1), scan(shape, True, 2)
    result = align_part_pair(up, fl)
    _assert_recovered(result, (t_up, t_fl))
    pair = result.alignments[1]
    assert pair.flipped and pair.yaw_determined and pair.rmse_mm < 0.5 and pair.coverage > 0.9
    assert result.metric_status == METRIC_STATUS
    # Outside covered on all sides: top from the upright scan, bottom from the flipped scan.
    assert min(result.surface_coverage.values()) > 0.85, result.surface_coverage
    height = 80.0 if shape is body else 15.0
    z = result.points[:, 2]
    assert ((result.source_index == 0) & (z > height - 0.5)).sum() > 300
    assert ((result.source_index == 1) & (z < 0.5)).sum() > 300
    assert result.colors is not None and len(result.colors) == len(result.points)
    # Traceability: every merged point is its source scan's input row, transformed.
    for i, source in enumerate((up, fl)):
        rows = result.point_index[result.source_index == i]
        expected = _apply(result.alignments[i].matrix, source.points[rows])
        assert np.allclose(expected, result.points[result.source_index == i])


def test_n_scans_general_api():
    scans = [scan(body, False, 1), scan(body, True, 2), scan(body, False, 3)]
    result = align_scans([s for s, _ in scans])
    assert [a.flipped for a in result.alignments] == [False, True, False]
    for index in (1, 2):
        _assert_recovered(result, [t for _, t in scans], index)


@pytest.mark.parametrize(
    ("options", "reason"),
    [
        ({"r": 43.0}, "section mismatch"),
        ({"h": 90.0}, "height mismatch"),
        ({"scale_error": 1.05}, "height mismatch"),
        ({"keep_frac": 0.1}, "object not found on the mat"),
    ],
    ids=["radius+3mm", "height+10mm", "scale+5pct", "floating-partial-scan"],
)
def test_wrong_object_scale_or_overlap_refused(options, reason):
    with pytest.raises(MultiScanAlignmentError, match=reason):
        align_part_pair(scan(body, False, 1)[0], scan(body, True, 2, **options)[0])


def test_different_part_and_closure_scale_error_refused():
    with pytest.raises(MultiScanAlignmentError, match="height mismatch"):
        align_part_pair(scan(body, False, 1)[0], scan(closure, True, 2)[0])
    with pytest.raises(MultiScanAlignmentError, match="section mismatch"):
        align_part_pair(scan(closure, False, 1)[0], scan(closure, True, 2, scale_error=1.05)[0])


def test_180_degree_yaw_error_refused_by_gate():
    (up, _), (fl, _) = scan(body, False, 1), scan(body, True, 2)
    good = align_part_pair(up, fl)
    relative = good.alignments[1].relative
    assert check_alignment(up, fl, relative, True).coverage > 0.95
    side = good.points[(good.points[:, 2] > 5) & (good.points[:, 2] < 75)]
    low, high = np.percentile(side[:, :2], [1, 99], axis=0)
    centre = np.r_[(low + high) / 2, 0]
    half_turn = _rot([0, 0, 1], np.pi)
    turn = _hom(half_turn, centre - half_turn @ centre)
    with pytest.raises(MultiScanAlignmentError, match="side-wall coverage"):
        check_alignment(up, fl, turn @ relative, True)


def test_wrong_role_refused():
    (up, _), (fl, _) = scan(body, False, 1), scan(body, True, 2, role="wrong")
    with pytest.raises(MultiScanAlignmentError, match="does not align"):
        align_scans([up, fl])
    # A lid's outer wall is top/bottom symmetric; only seen free space exposes the wrong flip.
    (up, _), (fl, _) = scan(closure, False, 1), scan(closure, True, 2, role="wrong")
    with pytest.raises(MultiScanAlignmentError, match="free-space conflict"):
        align_scans([up, fl])


def test_unknown_role_closure_resolved_by_free_space():
    (up, t_up) = scan(closure, False, 1, role="unknown")
    (fl, t_fl) = scan(closure, True, 2, role="unknown")
    result = align_scans([up, fl])
    assert result.alignments[1].flipped
    assert result.alignments[1].free_space_conflict < 0.01
    _assert_recovered(result, (t_up, t_fl))


def test_unknown_role_resolved_only_when_clear():
    (up, t_up), (fl, t_fl) = (
        scan(body, False, 1, role="unknown"),
        scan(body, True, 2, role="unknown"),
    )
    result = align_scans([up, fl])
    assert result.alignments[1].flipped and result.alignments[1].pose_margin >= 0.03
    _assert_recovered(result, (t_up, t_fl))
    plain_up = scan(cylinder, False, 1, role="unknown")[0]
    plain_fl = scan(cylinder, True, 2, role="unknown")[0]
    with pytest.raises(MultiScanAlignmentError, match="role ambiguous"):
        align_scans([plain_up, plain_fl])


def test_symmetric_part_flags_undetermined_yaw():
    (up, t_up), (fl, t_fl) = scan(cylinder, False, 1), scan(cylinder, True, 2)
    result = align_part_pair(up, fl)
    assert not result.alignments[1].yaw_determined
    # Geometry still lands: check tilt and axis position only, yaw is arbitrary by design.
    d = np.linalg.inv(result.alignments[0].matrix @ t_up) @ (result.alignments[1].matrix @ t_fl)
    rotation = d[:3, :3] / np.cbrt(np.linalg.det(d[:3, :3]))
    assert np.degrees(np.arccos(np.clip(rotation[2, 2], -1, 1))) < 1.0
    assert np.linalg.norm(d[:3, 3]) < 0.5


def test_floating_strays_give_correct_pose_or_refusal():
    (up, t_up), (fl, t_fl) = scan(body, False, 1, floaters=200), scan(body, True, 2, floaters=200)
    try:
        result = align_part_pair(up, fl)
    except MultiScanAlignmentError:
        return
    _assert_recovered(result, (t_up, t_fl))


@pytest.mark.parametrize(
    "options",
    [{"tilt_deg": 1.5}, {"tilt_deg": -2.0}, {"subsample": 0.85}],
    ids=["mat-tilt+1.5deg", "mat-tilt-2deg", "subsample-85pct"],
)
def test_mat_pose_errors_and_subsampling_still_recover(options):
    up, t_up = scan(body, False, 1, tilt_deg=0.0 if "tilt_deg" in options else None)
    fl, t_fl = scan(body, True, 2, **options)
    _assert_recovered(align_part_pair(up, fl), (t_up, t_fl))


def test_invalid_inputs_refused():
    up = scan(body, False, 1)[0]
    with pytest.raises(MultiScanAlignmentError, match="colors"):
        align_part_pair(up, ScanInput("bad", up.points, colors=np.zeros((3, 3))))
    shear = np.eye(4)
    shear[0, 1] = 0.5
    with pytest.raises(MultiScanAlignmentError, match="similarity"):
        align_part_pair(up, ScanInput("bad", up.points, to_mat_mm=shear))


def test_deterministic():
    up, fl = scan(closure, False, 1)[0], scan(closure, True, 2)[0]
    first, second = align_part_pair(up, fl), align_part_pair(up, fl)
    assert np.array_equal(first.points, second.points)
    assert np.array_equal(first.point_index, second.point_index)
    assert np.array_equal(first.alignments[1].matrix, second.alignments[1].matrix)


def _yaw_tilt_shift(result, truths):
    d = np.linalg.inv(result.alignments[0].matrix @ truths[0]) @ (
        result.alignments[1].matrix @ truths[1]
    )
    rotation = d[:3, :3] / np.cbrt(np.linalg.det(d[:3, :3]))
    angle = np.degrees(np.arccos(np.clip((np.trace(rotation) - 1) / 2, -1, 1)))
    tilt = np.degrees(np.arccos(np.clip(rotation[2, 2], -1, 1)))
    return angle, tilt, float(np.linalg.norm(d[:3, 3]))


@pytest.mark.parametrize("shape", [body, closure])
@pytest.mark.parametrize("density", [0.5, 0.2, 0.1, 0.05])
@pytest.mark.parametrize("seeds", [(1, 2), (5, 6)])
def test_density_sweep_never_accepts_a_wrong_yaw(shape, density, seeds):
    """Point spacing drives eps / slices / distances. A non-round part is accepted only with its
    yaw pinned (within yaw_probe_deg); otherwise it is refused, never merged at a guessed yaw."""
    (up, t_up), (fl, t_fl) = (
        scan(shape, False, seeds[0], density=density),
        scan(shape, True, seeds[1], density=density),
    )
    try:
        result = align_part_pair(up, fl)
    except MultiScanAlignmentError as error:
        assert density < 0.5 and "yaw undetermined" in str(error)
        return
    yaw, tilt, shift = _yaw_tilt_shift(result, (t_up, t_fl))
    pair = result.alignments[1]
    assert pair.yaw_determined and pair.yaw_uncertainty_deg <= 5.0
    assert yaw < 5.0 and tilt < 1.0 and shift < 0.5, (yaw, tilt, shift)
    if density == 0.5:
        assert yaw < 1.0


@pytest.mark.parametrize("seeds", [(1, 2), (3, 4), (10, 11), (20, 21)])
def test_sparse_boss_body_aligns_within_5_degrees_or_is_refused(seeds):
    up, t_up = scan(body, False, seeds[0], density=0.05)
    fl, t_fl = scan(body, True, seeds[1], density=0.05)
    try:
        result = align_part_pair(up, fl)
    except MultiScanAlignmentError as error:
        assert "yaw undetermined" in str(error)
        return
    assert _yaw_tilt_shift(result, (t_up, t_fl))[0] < 5.0


def test_round_part_is_accepted_with_yaw_flagged_at_sparse_density():
    up, t_up = scan(cylinder, False, 1, density=0.05)
    fl, t_fl = scan(cylinder, True, 2, density=0.05)
    result = align_part_pair(up, fl)
    assert not result.alignments[1].yaw_determined
    _, tilt, shift = _yaw_tilt_shift(result, (t_up, t_fl))
    assert tilt < 1.0 and shift < 0.5


def test_object_selection_ignores_off_mat_clutter_and_joins_split_wall():
    """The part standing on the mat wins over a bigger box beside the mat; a side wall split by
    an unreconstructed band (two clusters) is joined back over the same footprint."""
    up, t_up = scan(body, False, 1, clutter=True, wall_gap=True)
    fl, t_fl = scan(body, True, 2, clutter=True, wall_gap=True)
    result = align_part_pair(up, fl)
    _assert_recovered(result, (t_up, t_fl))
    assert np.ptp(result.points[:, 0]) < 100  # no clutter merged in


def test_rigid_moved_subsampled_copy_self_aligns_with_invariant_shell():
    """Same geometry, rigidly moved and 85 % subsampled: same side wall, exact alignment."""
    original, _ = scan(body, False, 1, density=0.2)
    rng = np.random.default_rng(9)
    motion = _hom(_rot(rng.normal(size=3), 2.0), rng.normal(size=3))
    keep = rng.random(len(original.points)) < 0.85
    copy = ScanInput(
        "copy",
        _apply(motion, original.points)[keep],
        original.colors[keep],
        mm_per_unit=original.mm_per_unit,
        flipped=False,
    )
    limits = AlignmentThresholds()
    a, b = prepare_scan(original, limits), prepare_scan(copy, limits)
    assert abs(len(b.shell) / len(a.shell) / 0.85 - 1) < 0.08  # frame-invariant side wall
    result = align_scans([original, copy])
    pair = result.alignments[1]
    assert not pair.flipped and pair.coverage > 0.9
    sample = original.points[keep][::40]
    moved = _apply(result.alignments[0].matrix, sample)
    copied = _apply(pair.matrix, _apply(motion, sample))
    assert np.median(np.linalg.norm(moved - copied, axis=1)) < 0.2


# ---------------------------------------------------------------- real-data regressions (PL-0483)
# Owner's assembled flat-oval shampoo pair: a white glare halo on the mat joined the part (97 mm
# "diameter" at z = 6 under a 57 mm bottle), the upright build lacked its top 20 mm, and the
# oval fits itself turned 180 degrees, so only the label tells front from back.


def oval(rng, a=31.5, b=17.0, h=100.0):
    """Flat-oval bottle proxy: 63 x 34 mm elliptic prism as the owner's scans measured it
    (2-fold symmetric in shape)."""
    perimeter = np.pi * (3 * (a + b) - np.sqrt((3 * a + b) * (a + 3 * b)))
    n = int(rng.density * perimeter * h)
    t, z = rng.uniform(0, 2 * np.pi, n), rng.uniform(0, h, n)
    m = int(rng.density * np.pi * a * b)

    def disc(z0):
        u, r = rng.uniform(0, 2 * np.pi, m), np.sqrt(rng.uniform(0, 1, m))
        return np.c_[a * r * np.cos(u), b * r * np.sin(u), np.full(m, z0)]

    return h, {"side": np.c_[a * np.cos(t), b * np.sin(t), z], "top": disc(h), "bottom": disc(0)}


_PRINT = np.random.default_rng(2026).random((72, 40)) > 0.55  # text-like 5 deg x 3 mm blocks


def label(points):
    """Printed label all round: dark text blocks on a light purple ground (no period)."""
    angle = np.degrees(np.arctan2(points[:, 1] / 17.0, points[:, 0] / 31.5)) % 360
    ink = _PRINT[(angle // 5).astype(int) % 72, np.clip(points[:, 2] // 3, 0, 39).astype(int)]
    lum = np.where(ink, 0.25, 0.85)
    return np.c_[lum * 0.6, lum * 0.5, lum]


def plain(points):
    return np.tile([0.5, 0.4, 0.6], (len(points), 1))


def shaded(paint, light, k):
    """One side lit (``k`` = 0..1 brightness drop away from azimuth ``light``, object frame)."""

    def colours(points):
        azimuth = np.arctan2(points[:, 1] / 17.0, points[:, 0] / 31.5)
        return np.clip(paint(points) * (1 - k + k * np.cos(azimuth - light))[:, None], 0, 1)

    return colours


# A smooth ideal ellipse keeps wall coverage flat over about +-6 degrees of yaw, so these
# proxies use an 8 degree probe. Production keeps ``yaw_probe_deg`` = 5: the real bottle
# pinned 3.5 degrees, and a smooth oval at 5 is refused (yaw undetermined), never mis-yawed.
OVAL = AlignmentThresholds(yaw_probe_deg=8.0)


def test_oval_bottle_yaw_resolved_by_label_texture():
    (up, t_up), (fl, t_fl) = scan(oval, False, 1, paint=label), scan(oval, True, 2, paint=label)
    result = align_part_pair(up, fl, OVAL)
    _assert_recovered(result, (t_up, t_fl))
    assert result.alignments[1].yaw_determined


def test_oval_bottle_without_label_refuses_yaw_twin():
    """Same oval, flat colour: front and back are indistinguishable, so no guessed yaw."""
    with pytest.raises(MultiScanAlignmentError, match="yaw undetermined"):
        align_part_pair(scan(oval, False, 1)[0], scan(oval, True, 2)[0], OVAL)


@pytest.mark.parametrize("k", [0.1, 0.3, 0.5, 0.7])
@pytest.mark.parametrize("paint", [plain, label], ids=["plain", "label"])
def test_one_sided_lighting_never_yields_a_wrong_yaw(paint, k):
    """Lit front in one scan, lit back in the other: shading must not pick the yaw. A plain
    oval is refused; a labelled one is aligned right or refused, never turned 180 degrees."""
    for seed in (1, 3):
        (up, t_up) = scan(oval, False, seed, paint=shaded(paint, 0.0, k))
        (fl, t_fl) = scan(oval, True, seed + 100, paint=shaded(paint, np.pi, k))
        try:
            result = align_part_pair(up, fl, OVAL)
        except MultiScanAlignmentError as error:
            assert "yaw undetermined" in str(error)
            continue
        assert paint is label, "a plain oval must never get a yaw"
        _assert_recovered(result, (t_up, t_fl))


def test_wrong_role_labelled_oval_refused():
    """The oval also fits itself upside down; the label then reads upside down, so neither
    the geometry nor the print may accept the wrong role."""
    up = scan(oval, False, 1, paint=label)[0]
    fl = scan(oval, True, 2, paint=label, role="wrong")[0]
    with pytest.raises(MultiScanAlignmentError):
        align_scans([up, fl], OVAL)


def test_oval_scale_error_refused_by_section_shape():
    up, fl = (
        scan(oval, False, 1, paint=label)[0],
        scan(oval, True, 2, paint=label, scale_error=1.05)[0],
    )
    with pytest.raises(MultiScanAlignmentError, match="section mismatch"):
        align_part_pair(up, fl)


def test_white_glare_halo_on_mat_is_not_part_of_the_object():
    up, t_up = scan(body, False, 1, halo=True)
    fl, t_fl = scan(body, True, 2, halo=True)
    part = prepare_scan(up, AlignmentThresholds())
    low = part.points[part.points[:, 2] < 6]
    centre = np.median(part.points[part.points[:, 2] > 20, :2], axis=0)
    assert np.linalg.norm(low[:, :2] - centre, axis=1).max() < 47  # r 40 (+ 4 mm boss foot)
    _assert_recovered(align_part_pair(up, fl), (t_up, t_fl))


def flared(rng):
    """Body whose white foot flares 5 mm out below 5 mm (petaloid / skirt base)."""
    height, faces = body(rng)
    faces["side"] = np.r_[faces["side"], _cyl(rng, 45, 0, 5), _disc(rng, 40, 45, 5)]
    faces["bottom"] = _disc(rng, 0, 45, 0)
    return height, faces


def white(points):
    return np.full((len(points), 3), 0.92)


def test_white_flared_foot_is_kept_not_cut_as_glare():
    up, t_up = scan(flared, False, 1, paint=white, halo=True)
    fl, t_fl = scan(flared, True, 2, paint=white, halo=True)
    part = prepare_scan(up, AlignmentThresholds())
    centre = np.median(part.points[part.points[:, 2] > 20, :2], axis=0)
    radius = np.linalg.norm(part.points[:, :2] - centre, axis=1)
    assert ((part.points[:, 2] < 5) & (radius > 44)).sum() > 100  # the foot wall stays
    _assert_recovered(align_part_pair(up, fl), (t_up, t_fl))


def test_scan_missing_its_top_is_refused_with_the_reason():
    up, fl = scan(body, False, 1, cut_top=15)[0], scan(body, True, 2)[0]
    with pytest.raises(
        MultiScanAlignmentError, match=r"upright-1 most likely misses the top 1[56] mm"
    ):
        align_part_pair(up, fl)


def bottle(rng, h=80.0, blob=0.0, open_top=False):
    """Bottle proxy: r 40 body with a side boss, r 37 foot 0-10 mm, shoulder at 65 mm, r 30 neck
    and cap to ``h``. ``blob``: an MVS blob that tall fused on the cap (sparse, 8 mm wide)."""
    _, faces = body(rng, r=40.0, h=65.0)
    faces["side"] = np.r_[_cyl(rng, 37, 0, 10), _cyl(rng, 40, 10, 65), _cyl(rng, 30, 65, h)]
    # ponytail: shoulder and foot steps are seen by both scans (as main's gate fixtures);
    # with each step seen only from its own side the gate's side-wall coverage drops
    # below 0.9 even for complete pairs (pre-existing, not the missing-end logic).
    faces["shoulder"] = np.r_[_disc(rng, 30, 40, 65), _disc(rng, 37, 40, 10)]
    faces["top"] = np.zeros((0, 3)) if open_top else _disc(rng, 0, 30, h)
    faces["bottom"] = _disc(rng, 0, 37, 0)
    if blob:
        n = int(rng.density * 200 * blob)
        a, r = rng.uniform(0, 2 * np.pi, n), rng.uniform(0, 8, n)
        faces["blob"] = np.c_[r * np.cos(a) + 10, r * np.sin(a), h + rng.uniform(0, blob, n)]
    return h, faces


def open_jar(rng, h=80.0):
    """Open jar body proxy: 4 mm rim, inner wall seen 15 mm down through the mouth (upright).
    (A 2 mm wall's inner face is within the shell's 2.5 mm outward test: pre-existing.)"""
    height, faces = body(rng, h=h)
    faces["top"] = np.r_[_disc(rng, 36, 40, h), _cyl(rng, 36, h - 15, h)]
    return height, faces


def necked(rng, nr=12.0, nh=8.0):
    """r 40 x 70 mm body with a short coaxial r ``nr`` x ``nh`` mm neck and its cap."""
    height, faces = body(rng, r=40.0, h=70.0)
    faces["side"] = np.r_[_cyl(rng, 40, 0, 70), _cyl(rng, nr, 70, 70 + nh)]
    faces["shoulder"] = _disc(rng, nr, 40, 70)
    faces["top"] = _disc(rng, 0, nr, 70 + nh)
    return 70 + nh, faces


def test_upside_down_scan_missing_its_base_is_completed_from_the_upright_scan():
    """Real Fast flipped build: 165 of 173 mm, its base end lost. Open end, walls agree."""
    (up, t_up), (fl, t_fl) = scan(bottle, False, 1), scan(bottle, True, 2, cut_top=8.0)
    result = align_part_pair(up, fl)
    _assert_recovered(result, (t_up, t_fl))
    pair = result.alignments[1]
    assert len(pair.limitations) == 1, pair.limitations
    assert (
        f"end completed from scan {up.scan_id}: scan {fl.scan_id} misses its free"
        in pair.limitations[0]
    )
    assert pair.free_space_conflict < 0.02  # the unseen end is not "seen empty" space
    heights = sorted(a.height_mm for a in result.alignments)
    assert abs(heights[0] - 72) < 1.0 and abs(heights[1] - 80) < 0.5, heights
    z = result.points[:, 2]
    assert z.max() > 78 and z.min() < 2.0  # walls to both ends (a mat side is never seen)


def test_upright_scan_missing_its_top_is_refused():
    """Its top is seen by no other scan: a lost cap and a different, taller part look alike."""
    up, fl = scan(bottle, False, 1, cut_top=8.0)[0], scan(bottle, True, 2)[0]
    with pytest.raises(MultiScanAlignmentError, match="not an upside-down scan"):
        align_part_pair(up, fl)


def test_closed_shorter_top_or_scale_error_is_still_refused_with_heights():
    with pytest.raises(MultiScanAlignmentError, match="saw a face closing its top") as error:
        align_part_pair(scan(body, False, 1)[0], scan(body, True, 2, h=88.0)[0])
    assert sorted(round(h) for h in error.value.heights_mm.values()) == [80, 88]
    with pytest.raises(MultiScanAlignmentError, match="section mismatch"):
        align_part_pair(
            scan(body, False, 1)[0], scan(body, True, 2, cut_top=8, scale_error=1.05)[0]
        )


@pytest.mark.parametrize("which", ["upright", "flipped"])
@pytest.mark.parametrize("error", [0.98, 1.02])
def test_two_percent_scale_with_an_open_end_is_refused(which, error):
    up = scan(bottle, False, 1, scale_error=error if which == "upright" else 1.0)[0]
    fl = scan(bottle, True, 2, cut_top=8, scale_error=error if which == "flipped" else 1.0)[0]
    with pytest.raises(MultiScanAlignmentError, match="differ in scale"):
        align_part_pair(up, fl)


def test_top_blob_does_not_move_the_mat_contact():
    """A 3 mm MVS blob on the cap + an 8 mm missing end: the blob is not the part's top."""
    (up, t_up) = scan(bottle, False, 1, blob=3.0)
    (fl, t_fl) = scan(bottle, True, 2, cut_top=8)
    result = align_part_pair(up, fl)
    angle, shift = _pose_error(result, (t_up, t_fl))
    assert angle < 1.0 and shift < 0.5, (angle, shift)
    assert abs(result.alignments[0].height_mm - 80) < 0.5


def tube(rng, h=80.0):
    """Open part whose inside the scan does not see (no top face, nothing inside)."""
    height, faces = body(rng, h=h)
    faces.pop("top")
    return height, faces


@pytest.mark.parametrize("taller", [88.0, 91.0])
@pytest.mark.parametrize(
    "shape", [open_jar, tube, lambda rng, h=80.0: bottle(rng, h, open_top=True)]
)
def test_taller_open_part_with_the_same_walls_is_refused(taller, shape):
    shape.__name__ = getattr(shape, "__name__", "open")
    up = scan(shape, False, 1)[0]
    fl = scan(bottle if shape.__name__ == "<lambda>" else shape, True, 2, h=taller)[0]
    with pytest.raises(MultiScanAlignmentError, match="not an upside-down scan"):
        align_part_pair(up, fl)


def test_straight_walled_lost_base_is_completed():
    """Owner's real case: flipped scan lost its base end, plain straight wall there."""
    (up, t_up), (fl, t_fl) = scan(body, False, 1), scan(body, True, 2, cut_top=8)
    result = align_part_pair(up, fl)
    _assert_recovered(result, (t_up, t_fl))
    assert "misses its free end" in result.alignments[1].limitations[0]


@pytest.mark.parametrize(("radius", "neck"), [(12, 4), (12, 8), (14, 6), (20, 8)])
def test_short_narrow_neck_counts_as_the_top(radius, neck):
    shape = lambda rng: necked(rng, radius, neck)  # noqa: E731
    shape.__name__ = "necked"
    (up, t_up), (fl, t_fl) = scan(shape, False, 1), scan(shape, True, 2)
    assert (
        abs(prepare_scan(replace(up, flipped=False), AlignmentThresholds()).height - 70 - neck)
        < 0.5
    )
    _assert_recovered(align_part_pair(up, fl), (t_up, t_fl))


def test_scale_bound_follows_the_scans_scale_uncertainty():
    up = scan(body, False, 1)[0]
    fl = scan(body, True, 2, scale_error=1.012)[0]
    with pytest.raises(MultiScanAlignmentError, match="differ in scale"):
        align_part_pair(up, fl)  # no uncertainty given: 1 % bound
    loose = [replace(s, scale_uncertainty=0.01) for s in (up, fl)]  # combined 1.4 %
    assert align_part_pair(*loose).alignments[1].limitations == ()
    with pytest.raises(MultiScanAlignmentError, match="differ in scale"):
        tight = [
            replace(s, scale_uncertainty=0.007)
            for s in (up, scan(body, True, 2, scale_error=1.02)[0])
        ]
        align_part_pair(*tight)


@pytest.mark.parametrize("error", [0.98, 1.02])
def test_two_percent_scale_within_the_height_tolerance_is_refused(error):
    """Open jar, no cut: the 1.6 mm height gap hides in the tolerance; the walls show it."""
    up, fl = scan(open_jar, False, 1)[0], scan(open_jar, True, 2, scale_error=error)[0]
    with pytest.raises(MultiScanAlignmentError, match="differ in scale"):
        align_part_pair(up, fl)


def spout(rng, h=80.0, offset=20.0):
    """r 40 x 70 mm body with an off-axis r 12 spout to ``h`` (its own cap)."""
    height, faces = body(rng, r=40.0, h=70.0)
    faces["spout"] = np.r_[_cyl(rng, 12, 70, h), _disc(rng, 0, 12, h)] + [offset, 0, 0]
    return h, faces


@pytest.mark.parametrize("tall", [76.0, 78.0, 80.0, 85.0])
def test_off_axis_spout_counts_as_the_top(tall):
    shape = lambda rng: spout(rng, tall)  # noqa: E731
    shape.__name__ = "spout"
    (up, t_up), (fl, t_fl) = scan(shape, False, 1), scan(shape, True, 2)
    height = prepare_scan(replace(up, flipped=False), AlignmentThresholds()).height
    assert abs(height - tall) < 0.5, height
    if tall <= 78:  # taller spouts: main's wall gate refuses this proxy pair too
        _assert_recovered(align_part_pair(up, fl), (t_up, t_fl))


@pytest.mark.parametrize("error", [0.985, 1.015, 1.02])
def test_large_claimed_scale_uncertainty_is_capped(error):
    up = replace(scan(bottle, False, 1)[0], scale_uncertainty=0.015)
    fl = replace(scan(bottle, True, 2, cut_top=8, scale_error=error)[0], scale_uncertainty=0.015)
    with pytest.raises(MultiScanAlignmentError, match="differ in scale"):
        align_part_pair(up, fl)


def test_sparse_outward_artifacts_do_not_replace_the_wall():
    """A sparse MVS glare fan 2-12 mm outside the wall (real scans: a few points per 3 mm)
    must not replace the outer wall under it: the shell stays on the r 40 cylinder."""
    from packlab_core.multiscan_alignment import _shell

    part = prepare_scan(scan(cylinder, False, 1)[0], AlignmentThresholds())
    centre = np.median(part.points[part.points[:, 2] > 20, :2], axis=0)
    rng = np.random.default_rng(5)
    a, r, z = rng.uniform(-0.5, 0.5, 100), rng.uniform(42, 52, 100), rng.uniform(20, 50, 100)
    fan = np.c_[centre[0] + r * np.cos(a), centre[1] + r * np.sin(a), z]
    shell = _shell(np.r_[part.points, fan], part.height, part.spacing, AlignmentThresholds())[0]
    rel = shell[:, :2] - centre
    radius = np.linalg.norm(rel, axis=1)
    wedge = (
        (np.abs(np.arctan2(rel[:, 1], rel[:, 0])) < 0.5) & (shell[:, 2] > 20) & (shell[:, 2] < 50)
    )
    # main: 118 wall / 81 fan points in the wedge; a few chance fan clusters may stay
    assert (wedge & (np.abs(radius - 40) < 1.5)).sum() > 300
    assert (wedge & (radius > 41.5)).sum() < 0.1 * wedge.sum()


def _lug(rng, width, height, proud, z0):
    """A ``width`` x ``height`` mm lug ``proud`` mm out of the r 40 wall, opposite the boss."""
    w = width / 2
    return np.r_[
        _rect(rng, 40 + proud, -w, w, z0, z0 + height),
        _wall(rng, -w, 38.7, 40 + proud, z0, z0 + height),
        _wall(rng, w, 38.7, 40 + proud, z0, z0 + height),
        _cap(rng, 39, 40 + proud, -w, w, z0),
        _cap(rng, 39, 40 + proud, -w, w, z0 + height),
    ] * [-1, 1, 1]


def lugged(width, height, proud, z0=40.0):
    def shape(rng):
        h, faces = body(rng)
        faces["lug"] = _lug(rng, width, height, proud, z0)
        return h, faces

    shape.__name__ = "lugged"
    return shape


def fuzzed(sigma):
    """Jar body whose wall opposite the boss (z 25-70) carries ``sigma`` mm MVS fuzz."""

    def shape(rng):
        h, faces = body(rng)
        side = faces["side"]
        at = (side[:, 0] < -30) & (side[:, 2] > 25) & (side[:, 2] < 70)
        side[at] += rng.rng.normal(0, sigma, (at.sum(), 3))
        return h, faces

    shape.__name__ = "fuzzed"
    return shape


def test_fuzz_in_one_scan_does_not_hide_a_lug_in_the_other():
    """Noise in one scan must never loosen the check: a 10 x 20 x 4 mm lug opposite a fuzzy
    patch of the other scan is still refused (V02 widened the tolerance with the noise)."""
    for sigma in (0.6, 0.9):
        with pytest.raises(MultiScanAlignmentError):
            align_part_pair(scan(fuzzed(sigma), False, 1)[0], scan(lugged(10, 20, 4.0), True, 2)[0])


def test_miss_patch_reads_true_area():
    """A one-scan 10 x 20 mm lug face (+ two 3 mm side walls) reads about its real area."""
    from packlab_core.multiscan_alignment import _apply, _miss_patch, _nearest, _prepare

    up, t_up = scan(body, False, 1)
    fl, t_fl = scan(lugged(10, 20, 3.0), True, 2)
    limits = AlignmentThresholds()
    ref, part = _prepare(up, limits), _prepare(fl, limits)
    # Ground-truth pose: flipped scan's mat frame -> reference mat frame.
    truth = ref.frame @ t_up @ np.linalg.inv(t_fl) @ np.linalg.inv(part.frame)
    truth[:3, :3] /= np.cbrt(np.linalg.det(truth[:3, :3]))
    area = _miss_patch(part, truth, ref, _nearest(ref.shell), limits)
    assert 150 < area < 380, area
    assert _apply(truth, part.shell).shape == part.shell.shape


def waisted(bump):
    """r 40 body narrowing to r 34 at z 40-50 through cones (z 30-40, z 50-60). ``bump``: a
    4 mm wide bump that far out on the upper cone, which faces the mat when flipped."""

    def shape(rng):
        h, faces = body(rng)
        side = faces["side"]
        side = side[(side[:, 2] < 30) | (side[:, 2] > 60)]

        def cone(z0, z1, r0, r1, a0=0.0, a1=2 * np.pi, out=0.0):
            n = int(rng.density * 37 * (a1 - a0) * (z1 - z0) * 1.1)
            a, z = rng.uniform(a0, a1, n), rng.uniform(z0, z1, n)
            r = r0 + (r1 - r0) * (z - z0) / (z1 - z0) + out
            return np.c_[r * np.cos(a), r * np.sin(a), z]

        pieces = [side, cone(30, 40, 40, 34), _cyl(rng, 34, 40, 50)]
        if bump:
            w = 4.0 / 37
            pieces += [
                cone(50, 60, 34, 40, 0, np.pi - w),
                cone(50, 60, 34, 40, np.pi + w, 2 * np.pi),
                cone(51, 59, 34.6, 39.4, np.pi - w, np.pi + w, out=bump),
            ]
        else:
            pieces.append(cone(50, 60, 34, 40))
        faces["side"] = np.r_[tuple(pieces)]
        return h, faces

    shape.__name__ = "waisted"
    return shape


def test_bump_on_a_mat_facing_slope_is_refused():
    """The upright scan sees a 4 mm bump on a slope the flipped scan sees facing the mat; the
    flipped (plain) slope still has to account for it."""
    with pytest.raises(MultiScanAlignmentError):
        align_part_pair(scan(waisted(4.5), False, 1)[0], scan(waisted(0.0), True, 2)[0])


def modified(**change):
    """Jar body proxy changed near an end (only one scan of a pair gets it): ``lug`` (z0, z1)
    a 4 mm x 18 mm lug opposite the boss, ``groove`` (dr, z0, z1), ``top`` (dr, depth)."""

    def shape(rng):
        height, faces = body(rng)
        side = faces["side"]
        cuts = []
        if "groove" in change:
            cuts.append(change["groove"])
        if "top" in change:
            dr, depth = change["top"]
            cuts.append((dr, height - depth, height))
        for dr, z0, z1 in cuts:
            inside = (side[:, 2] >= z0) & (side[:, 2] < z1)
            side = np.r_[side[~inside], _cyl(rng, 40 - dr, z0, z1), _disc(rng, 40 - dr, 40, z0)]
            if z1 < height:
                side = np.r_[side, _disc(rng, 40 - dr, 40, z1)]
        faces["side"] = side
        if "lug" in change:
            z0, z1 = change["lug"]
            faces["lug"] = np.r_[
                _rect(rng, 44, -9, 9, z0, z1),
                _wall(rng, -9, 38.7, 44, z0, z1),
                _wall(rng, 9, 38.7, 44, z0, z1),
                _cap(rng, 39, 44, -9, 9, z1),
            ] * [-1, 1, 1]
        return height, faces

    shape.__name__ = "modified"
    return shape


@pytest.mark.parametrize(
    "change",
    [
        {"lug": (4.0, 13.0)},  # near the flipped scan's free end (the part's base)
        {"lug": (68.0, 77.0)},  # near the flipped scan's mat contact
        {"groove": (3.0, 6.0, 12.0)},
        {"top": (2.0, 10.0)},  # a 2 mm step over the top 10 mm
    ],
)
def test_one_scan_feature_near_an_end_is_refused(change):
    up = scan(body, False, 1)[0]
    fl = scan(modified(**change), True, 2)[0]
    with pytest.raises(MultiScanAlignmentError):
        align_part_pair(up, fl)


def test_extra_boss_in_one_scan_only_is_refused():
    def two_bosses(rng):
        height, faces = body(rng)
        faces["boss2"] = np.r_[
            _rect(rng, 44, -11, 11, 30, 54),
            _wall(rng, -11, 38.7, 44, 30, 54),
            _wall(rng, 11, 38.7, 44, 30, 54),
            _cap(rng, 39, 44, -11, 11, 30),
            _cap(rng, 39, 44, -11, 11, 54),
        ] * [-1, 1, 1]
        return height, faces

    with pytest.raises(MultiScanAlignmentError, match="coverage"):
        align_part_pair(scan(two_bosses, False, 1)[0], scan(body, True, 2)[0])


def test_merge_keeps_one_scan_surfaces_inside_the_other_footprint():
    """Merge filter: a neck-ring underside one scan alone saw (r 40-44, inside the other scan's
    footprint) stays; mat glare 15-25 mm outside the other scan's footprint goes."""
    from packlab_core.multiscan_alignment import FOOTPRINT_CELL_MM, _in_footprint

    rng = _Gen(np.random.default_rng(3), 0.5)
    other = np.r_[_cyl(rng, 44, 0, 80), _disc(rng, 0, 44, 80)]  # the other scan's object points
    underside = _disc(rng, 40, 44, 70)
    a = rng.uniform(0, 2 * np.pi, 200)
    glare = np.c_[60 * np.cos(a), 60 * np.sin(a), rng.uniform(1, 4, 200)]
    inside = _in_footprint(other, FOOTPRINT_CELL_MM)
    assert inside(underside).all()
    assert not inside(glare).any()


def test_flipped_short_scan_of_a_different_top_is_refused():
    """Reviewer probe: bottle (r 30 neck above 65 mm) vs a plain body flipped, its free end
    lost. The neck lies in the flipped scan's contact zone; the sections still see it."""
    up = scan(bottle, False, 1, density=0.2)[0]
    fl = scan(body, True, 2, density=0.2, cut_top=8)[0]
    with pytest.raises(MultiScanAlignmentError, match="section mismatch"):
        align_part_pair(up, fl)


# ---------------------------------------------------------------- owner-confirmed override


def _override_offer(up, fl):
    with pytest.raises(MultiScanAlignmentError) as caught:
        align_part_pair(up, fl)
    return caught.value.override_disagreements


def test_override_is_offered_only_for_agreement_refusals():
    """Agreement gates on a determined pose: offered. Height, yaw between turns and a scale
    difference beyond OVERRIDE_MAX_SCALE: never."""

    def two_bosses(rng):
        height, faces = body(rng)
        faces["boss2"] = _lug(rng, 22, 24, 4.0, 30.0)
        return height, faces

    offer = _override_offer(scan(two_bosses, False, 1)[0], scan(body, True, 2)[0])
    assert offer and {item["kind"] for item in offer} <= {"coverage", "patch", "section", "scale"}
    assert _override_offer(scan(body, False, 1)[0], scan(body, True, 2, h=70.0)[0]) is None
    assert _override_offer(scan(oval, False, 1)[0], scan(oval, True, 2)[0]) is None  # yaw
    assert (
        _override_offer(scan(body, False, 1)[0], scan(body, True, 2, scale_error=1.03)[0]) is None
    )


def curtained(rng):
    """Labelled flat oval as an upside-down scan sees it on the owner's real pair: the top
    12 mm (on its mat) 1.5 mm smaller and an MVS curtain flaring 4 mm out at the tips below."""
    height, faces = oval(rng)
    side = faces["side"]
    top = side[:, 2] > height - 12
    side[top, 0] *= 30.0 / 31.5
    side[top, 1] *= 15.5 / 17.0
    n = int(rng.density * 35 * np.radians(120) * 8)
    t = rng.uniform(-np.pi / 6, np.pi / 6, n) + np.pi * (rng.uniform(0, 1, n) < 0.5)
    z = rng.uniform(height - 20, height - 12, n)
    grow = 1 + 4 * (z - (height - 20)) / 8 / 31.5
    faces["curtain"] = np.c_[31.5 * grow * np.cos(t), 17.0 * grow * np.sin(t), z]
    return height, faces


def test_owner_confirmed_merge_takes_the_top_from_the_upright_scan():
    up, t_up = scan(oval, False, 1, paint=label)
    fl, t_fl = scan(curtained, True, 2, paint=label)
    offer = _override_offer(up, fl)
    assert offer, "a same-part pair refused on agreement only must offer the override"
    result = align_part_pair(up, fl, owner_confirmed=True)
    _assert_recovered(result, (t_up, t_fl))
    assert result.verification == "OWNER_CONFIRMED_UNVERIFIED" and result.disagreements
    assert result.metric_status == METRIC_STATUS
    assert any("OWNER_CONFIRMED_UNVERIFIED" in text for text in result.alignments[1].limitations)
    from packlab_core.multiscan_alignment import _section

    p, src = result.points, result.source_index
    assert (src[p[:, 2] > 75] == 0).all()  # the top (the upside-down scan's mat side): upright
    body_width = _section(p, 50.0, 10.0)[1]
    assert _section(p, 84.0, 3.0)[1] < body_width + 1.0  # no curtain at the tips
    assert _section(p, 93.0, 3.0)[1] > 62.0  # upright top: 63 mm long axis, not 60
    assert ((src == 1) & (p[:, 2] < 5)).sum() > 300  # base from the upside-down scan
