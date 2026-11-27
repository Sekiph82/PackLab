"""PL-0492 oval / rounded-rectangle section fit on synthetic bottles with known dimensions.

The fixtures are generated surfaces (exact superellipse walls, optional Gaussian noise, a
missing side patch, a base disc and a few far outliers). Passing proves the fit recovers
these known dimensions and refuses unsupported shapes; it is not physical validation.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from packlab_core.oval_section_fit import (
    ARC_POINTS,
    OvalFitRefusal,
    SectionShapeClass,
    fit_oval_sections,
    section_outline,
)


def bottle(
    a: float,
    b: float,
    n: float,
    *,
    height: float = 160.0,
    neck: float = 12.0,
    angle: float = 30.0,
    noise: float = 0.0,
    hole: bool = False,
    twist: float = 0.0,
    ribs: float = 0.0,
    seed: int = 1,
) -> np.ndarray:
    """Body to 70 % of the height, shoulder to 85 %, round neck; rotated and offset."""
    rng = np.random.default_rng(seed)
    points = []
    for z in np.linspace(0.0, height, 200):
        f = z / height
        if f < 0.7:
            aa, bb, nn = a, b, n
        elif f < 0.85:
            t = (f - 0.7) / 0.15
            aa, bb, nn = a + (neck - a) * t, b + (neck - b) * t, n + (2 - n) * t
        else:
            aa = bb = neck
            nn = 2.0
        rotate = math.radians(twist * f)
        for t in np.linspace(0.0, math.tau, 120, endpoint=False):
            if hole and 0.3 < f < 0.5 and 0.0 < t < 2.5:
                continue  # a side patch the photos never saw
            c, s = math.cos(t), math.sin(t)
            scale = 1.0 + ribs * math.cos(8 * t)
            x = scale * aa * math.copysign(abs(c) ** (2 / nn), c)
            y = scale * bb * math.copysign(abs(s) ** (2 / nn), s)
            points.append(
                (
                    x * math.cos(rotate) - y * math.sin(rotate),
                    x * math.sin(rotate) + y * math.cos(rotate),
                    z,
                )
            )
    for r in np.linspace(0.0, 0.9, 10):  # closed base disc (reconstructed underside)
        for t in np.linspace(0.0, math.tau, 60, endpoint=False):
            points.append((r * a * math.cos(t), r * b * math.sin(t), 0.0))
    cloud = np.asarray(points)
    theta = math.radians(angle)
    rotation = np.array([[math.cos(theta), -math.sin(theta)], [math.sin(theta), math.cos(theta)]])
    cloud[:, :2] = cloud[:, :2] @ rotation.T + (3.0, -2.0)
    cloud += rng.normal(0.0, noise, cloud.shape)
    if noise:
        cloud = np.vstack([cloud, rng.uniform((-80, -80, 0), (80, 80, height), (40, 3))])
    return cloud


@pytest.mark.parametrize(
    ("a", "b", "n", "expected"),
    [
        (25.0, 25.0, 2.0, SectionShapeClass.ROUND),
        (30.0, 20.0, 2.0, SectionShapeClass.OVAL),
        (30.0, 16.5, 2.0, SectionShapeClass.OVAL),
        (30.0, 20.0, 4.0, SectionShapeClass.ROUNDED_RECTANGLE),
    ],
)
@pytest.mark.parametrize(("noise", "hole"), [(0.0, False), (0.3, True)])
def test_known_bottles_are_recovered(a, b, n, expected, noise, hole) -> None:
    fit = fit_oval_sections(bottle(a, b, n, noise=noise, hole=hole))
    tolerance = 0.05 if not noise else 0.5
    assert fit.classification is expected
    assert fit.width == pytest.approx(2 * a, abs=tolerance)
    assert fit.depth == pytest.approx(2 * b, abs=tolerance)
    assert fit.height == pytest.approx(160.0, abs=0.05 if not noise else 1.5)
    assert fit.neck_diameter == pytest.approx(24.0, abs=tolerance)
    if expected is not SectionShapeClass.ROUND:
        assert (fit.orientation_deg - 30.0 + 90.0) % 180.0 - 90.0 == pytest.approx(0.0, abs=1.0)
    if expected is SectionShapeClass.ROUNDED_RECTANGLE:
        assert fit.exponent == pytest.approx(4.0, abs=0.3)
    names = [name for name, _z0, _z1 in fit.zones]
    assert names[-3:] == ["body", "shoulder", "neck"]
    body = next(item for item in fit.zones if item[0] == "body")
    assert body[2] == pytest.approx(112.0, abs=5.0)  # body ends at 70 % of 160 mm
    zs = [item.z for item in fit.sections]
    assert zs[0] == 0.0 and zs == sorted(zs) and len(zs) <= 16
    report = fit.as_dict()
    assert report["scale_state"] == "METRIC_UNVERIFIED"
    assert report["physical_accuracy_validation_status"] == "DEFERRED_OWNER_VALIDATION"
    assert report["thresholds"]["round_min_aspect"] == 0.95


def test_hole_slices_are_flagged_not_invented() -> None:
    cloud = bottle(30.0, 20.0, 2.0)
    side = (cloud[:, 0] > 3.0) | (cloud[:, 1] > -2.0)  # three quarters of the ring unseen
    cloud = cloud[~((cloud[:, 2] > 50) & (cloud[:, 2] < 80) & side)]
    fit = fit_oval_sections(cloud)
    assert fit.width == pytest.approx(60.0, abs=0.5)
    assert any(not item.observed for item in fit.slices)
    assert any("interpolated" in note for note in fit.notes)


def test_refusals_are_typed() -> None:
    with pytest.raises(OvalFitRefusal) as small:
        fit_oval_sections(np.zeros((10, 3)))
    assert small.value.code == "scan_too_small"
    with pytest.raises(OvalFitRefusal) as ribbed:
        fit_oval_sections(bottle(30.0, 20.0, 2.0, ribs=0.12))
    assert ribbed.value.code == "section_not_round_or_oval"
    with pytest.raises(OvalFitRefusal) as twisted:
        fit_oval_sections(bottle(30.0, 18.0, 2.0, twist=60.0))
    assert twisted.value.code in {"orientation_inconsistent", "section_not_round_or_oval"}
    sparse = bottle(30.0, 20.0, 2.0)
    sparse = sparse[(sparse[:, 0] - 3.0) > 15.0]  # one side only: no section is closed
    with pytest.raises(OvalFitRefusal) as unseen:
        fit_oval_sections(sparse)
    assert unseen.value.code == "insufficient_observed_sections"


def test_section_outline_is_compatible_and_has_flat_panels() -> None:
    for a, b, n in ((30.0, 20.0, 2.0), (30.0, 20.0, 4.0), (11.0, 10.3, 2.0)):
        outline = np.asarray(section_outline(a, b, n))
        assert len(outline) == 2 * ARC_POINTS + 4
        x, y = outline[:, 0], outline[:, 1]
        assert 0.5 * float(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) > 0  # CCW
        assert outline[0, 1] == outline[1, 1] == b and outline[0, 0] == -outline[1, 0] > 0
        assert x.max() == pytest.approx(a, abs=1e-6) and np.abs(y).max() == pytest.approx(b)
    with pytest.raises(ValueError):
        section_outline(0.0, 1.0, 2.0)


def _tilted(cloud: np.ndarray, degrees: float, axis: int) -> np.ndarray:
    t = math.radians(degrees)
    c, s = math.cos(t), math.sin(t)
    rotation = (
        np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
        if axis == 0
        else np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
    )
    return np.asarray(cloud @ rotation.T)


@pytest.mark.parametrize("axis", [0, 1])
def test_tilted_scan_is_relevelled_to_the_upright_dimensions(axis) -> None:
    upright = fit_oval_sections(bottle(31.0, 17.0, 2.0))
    tilted = fit_oval_sections(_tilted(bottle(31.0, 17.0, 2.0), 5.0, axis))
    assert upright.tilt_deg == pytest.approx(0.0, abs=0.5)
    assert tilted.tilt_deg == pytest.approx(5.0, abs=0.3)
    for name in ("width", "depth", "height", "neck_diameter"):
        assert getattr(tilted, name) == pytest.approx(getattr(upright, name), abs=0.3), name
    assert tilted.width == pytest.approx(62.0, abs=0.3)
    assert any("re-levelled" in note for note in tilted.notes)
    frame = tilted.as_dict()["scan_master_to_design_frame"]
    rotation = np.asarray(frame["first_rotate_row_major"]).reshape(3, 3)
    assert rotation @ rotation.T == pytest.approx(np.eye(3), abs=1e-6)


def test_strongly_tilted_scan_is_refused() -> None:
    with pytest.raises(OvalFitRefusal) as leaning:
        fit_oval_sections(_tilted(bottle(31.0, 17.0, 2.0), 25.0, 0))
    assert leaning.value.code == "scan_not_upright"
