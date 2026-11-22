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
    MultiScanAlignmentError,
    ScanInput,
    align_part_pair,
    align_scans,
)

DENSITY = 0.5  # points per mm^2


def _cyl(rng, r, z0, z1, a0=0.0, a1=2 * np.pi):
    n = int(DENSITY * r * (a1 - a0) * (z1 - z0))
    a, z = rng.uniform(a0, a1, n), rng.uniform(z0, z1, n)
    return np.c_[r * np.cos(a), r * np.sin(a), z]


def _disc(rng, r0, r1, z):
    n = int(DENSITY * np.pi * (r1**2 - r0**2))
    a, r = rng.uniform(0, 2 * np.pi, n), np.sqrt(rng.uniform(r0**2, r1**2, n))
    return np.c_[r * np.cos(a), r * np.sin(a), np.full(n, z)]


def _rect(rng, x, y0, y1, z0, z1):  # plane x = const
    n = int(DENSITY * (y1 - y0) * (z1 - z0))
    return np.c_[np.full(n, x), rng.uniform(y0, y1, n), rng.uniform(z0, z1, n)]


def _wall(rng, y, x0, x1, z0, z1):  # plane y = const
    return _rect(rng, 0, x0, x1, z0, z1)[:, [1, 0, 2]] + [0, y, 0]


def _cap(rng, x0, x1, y0, y1, z):  # plane z = const
    n = int(DENSITY * (x1 - x0) * (y1 - y0))
    return np.c_[rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), np.full(n, z)]


def body(rng):
    """Jar body proxy: r 40, h 80, off-centre 20x30x4 mm side boss (fixes yaw and height)."""
    return 80.0, {
        "side": _cyl(rng, 40, 0, 80),
        "boss": np.r_[
            _rect(rng, 44, -10, 10, 15, 45),
            _wall(rng, -10, 38.7, 44, 15, 45),
            _wall(rng, 10, 38.7, 44, 15, 45),
            _cap(rng, 39, 44, -10, 10, 15),
            _cap(rng, 39, 44, -10, 10, 45),
        ],
        "top": _disc(rng, 0, 40, 80),
        "bottom": _disc(rng, 0, 40, 0),
    }


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


def scan(shape, flipped, seed, keep_frac=1.0):
    """Return (ScanInput, object->camera-units 4x4) for an upright or upside-down capture."""
    rng = np.random.default_rng(seed)
    height, faces = shape(rng)
    hidden = "top" if flipped else "bottom"  # face on the mat is not seen
    obj = np.concatenate([p for name, p in faces.items() if name != hidden])
    if keep_frac < 1.0:  # only the part of the object nearest the camera (top in mat frame)
        z_mat = height - obj[:, 2] if flipped else obj[:, 2]
        obj = obj[z_mat > (1 - keep_frac) * height]
    place = _hom(_rot([0, 0, 1], rng.uniform(0, 2 * np.pi)), [*rng.uniform(-30, 30, 2), 0])
    if flipped:
        place = place @ _hom(_rot([1, 0, 0], np.pi), [0, 0, height])
    mat = np.c_[rng.uniform(-148, 148, 18000), rng.uniform(-105, 105, 18000), np.zeros(18000)]
    pts = np.r_[_apply(place, obj), mat] + rng.normal(0, 0.15, (len(obj) + 18000, 3))
    scale = rng.uniform(0.01, 0.05)  # camera units per mm
    camera = _hom(_rot(rng.normal(size=3), rng.uniform(0, np.pi)), rng.normal(size=3), scale)
    colors = np.tile([0.2, 0.4, 0.6], (len(pts), 1))
    sid = f"{shape.__name__}-{'flipped' if flipped else 'upright'}-{seed}"
    scan_input = ScanInput(sid, _apply(camera, pts), colors, mm_per_unit=1 / scale, flipped=flipped)
    return scan_input, camera @ place


def _pose_error(result, truths):
    e = result.alignments[0].matrix @ truths[0]
    g = result.alignments[1].matrix @ truths[1]
    d = np.linalg.inv(e) @ g
    angle = np.degrees(np.arccos(np.clip((np.trace(d[:3, :3]) - 1) / 2, -1, 1)))
    return angle, float(np.linalg.norm(d[:3, 3]))


@pytest.mark.parametrize("shape", [body, closure])
def test_upright_and_flipped_pair_recovers_known_transform(shape):
    (up, t_up), (fl, t_fl) = scan(shape, False, 1), scan(shape, True, 2)
    result = align_part_pair(up, fl)
    angle, shift = _pose_error(result, (t_up, t_fl))
    assert angle < 1.0 and shift < 0.5, (angle, shift)
    assert result.alignments[1].flipped
    assert result.alignments[1].rmse_mm < 0.5
    assert result.metric_status == METRIC_STATUS
    height = 80.0 if shape is body else 15.0
    z = result.points[:, 2]
    # Closed outside: top from the upright scan, bottom (mat side) from the flipped scan.
    assert ((result.source_index == 0) & (z > height - 0.5)).sum() > 500
    assert ((result.source_index == 1) & (z < 0.5)).sum() > 300
    assert result.colors is not None and len(result.colors) == len(result.points)


def test_n_scans_general_api():
    scans = [scan(body, False, 1), scan(body, True, 2), scan(body, False, 3)]
    result = align_scans([s for s, _ in scans])
    assert [a.flipped for a in result.alignments] == [False, True, False]
    for index in (1, 2):
        angle, shift = _pose_error(
            type(result)(
                result.reference_id,
                (result.alignments[0], result.alignments[index]),
                result.points,
                result.colors,
                result.source_index,
            ),
            (scans[0][1], scans[index][1]),
        )
        assert angle < 1.0 and shift < 0.5


def test_different_object_refused():
    with pytest.raises(MultiScanAlignmentError, match="does not align"):
        align_part_pair(scan(body, False, 1)[0], scan(closure, True, 2)[0])


def test_too_little_overlap_refused():
    with pytest.raises(MultiScanAlignmentError, match="overlap"):
        align_part_pair(scan(body, False, 1)[0], scan(body, True, 2, keep_frac=0.1)[0])


def test_deterministic():
    up, fl = scan(closure, False, 1)[0], scan(closure, True, 2)[0]
    first, second = align_part_pair(up, fl), align_part_pair(up, fl)
    assert np.array_equal(first.points, second.points)
    assert np.array_equal(first.source_index, second.source_index)
    assert np.array_equal(first.alignments[1].matrix, second.alignments[1].matrix)
