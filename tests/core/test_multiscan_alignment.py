"""PL-0483 multi-scan alignment on SYNTHETIC PROXY shapes only (no real-accuracy claim).

Shapes have known metric ground truth (mm); each scan = visible faces + A4 mat plane + noise,
placed on the mat at a random yaw/offset and seen through a random similarity (camera units).
"""

from __future__ import annotations

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
    **shape_args,
):
    """Return (ScanInput, object->camera-units 4x4) for an upright or upside-down capture.

    tilt_deg: pass ``to_mat_mm`` from the true mat pose with that tilt error added.
    scale_error: multiplies the mm_per_unit handed to the aligner.
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
    place = _hom(_rot([0, 0, 1], rng.uniform(0, 2 * np.pi)), [*rng.uniform(-30, 30, 2), 0])
    if flipped:
        place = place @ _hom(_rot([1, 0, 0], np.pi), [0, 0, height])
    count = int(18000 * density / 0.5)
    mat = np.c_[rng.uniform(-148, 148, count), rng.uniform(-105, 105, count), np.zeros(count)]
    pts = np.r_[_apply(place, obj), mat] + rng.normal(0, 0.15, (len(obj) + count, 3))
    if clutter:  # a bigger box standing on the table beside (not on) the A4 mat
        box = rng.uniform([170, -60, 0], [260, 60, 60], (int(20000 * density), 3))
        pts = np.r_[pts, box]
    if floaters:  # MVS-like stray points floating above the part
        pts = np.r_[pts, rng.uniform([-60, -60, height + 5], [60, 60, height + 60], (floaters, 3))]
    if subsample < 1.0:
        pts = pts[rng.random(len(pts)) < subsample]
    scale = rng.uniform(0.01, 0.05)  # camera units per mm
    camera = _hom(_rot(rng.normal(size=3), rng.uniform(0, np.pi)), rng.normal(size=3), scale)
    colors = np.tile([0.2, 0.4, 0.6], (len(pts), 1))
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
        ({"r": 43.0}, "diameter mismatch"),
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
    with pytest.raises(MultiScanAlignmentError, match="diameter mismatch"):
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
        assert density < 0.5 and "yaw undetermined on a non-symmetric part" in str(error)
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
