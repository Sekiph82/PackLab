"""Non-round (oval / rounded-rectangle) cross-section fit of an upright Scan Master (PL-0492).

The revolved Design Model assumes one radius per height; a flat-oval bottle has two. This
module fits one section per height band in the Scan Master's base-levelled frame (z up):

* a robust direct ellipse fit (Halir-Flusser on normalized points, seeded least median of
  Sampson distances, trimmed refit), then
* a superellipse ``|x/a|^n + |y/b|^n = 1`` in the ellipse frame (``n = 2`` is the ellipse,
  ``n`` towards 4+ a rounded rectangle), scored by the radial residual.

Per-slice parameters are re-expressed in one common orientation (circular mean of the
major-axis angles), smoothed along the height (median of 3), and slices without enough
evidence (holes, < ``MIN_SLICE_COVERAGE`` of the circumference) are interpolated and
flagged, never invented beyond the observed height. Zones (base, body, shoulder, neck) come
from the smoothed half-axes like the revolved profile zones. The shape is classified ROUND /
OVAL / ROUNDED_RECTANGLE with the fixed thresholds below, or refused with a typed reason.

Pure numpy, no authority: the caller binds the result to a Scan Master lineage. Values are
in the Scan Master unit (``mm_unverified``, METRIC_UNVERIFIED); nothing here is physical
validation.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

import numpy as np

METHOD = "halir_flusser_lmeds_sampson_superellipse_radial_v1"
SEED = 0
SLICE_COUNT = 40
MIN_SLICE_POINTS = 24
MIN_SLICE_COVERAGE = 0.40  # of 36 ten-degree bins, each with >= 2 points
MIN_BODY_SLICES = 4
ROUND_MIN_ASPECT = 0.95  # minor/major at or above: round
RECTANGLE_MIN_EXPONENT = 2.6  # superellipse exponent at or above: rounded rectangle
MAX_RELATIVE_RESIDUAL = 0.03  # median radial RMS / half-major on the body
MAX_ORIENTATION_SPREAD_DEG = 10.0
LEVEL_TOLERANCE_DEG = 0.5  # body-centre drift below this angle counts as upright
MAX_TILT_DEG = 15.0  # a larger axis tilt is refused: the Scan Master base needs levelling
MAX_TILT_STDERR_DEG = 1.0  # tilt standard error above this: axis not determined, refuse
LEVEL_ITERATIONS = 4
SECTION_TOLERANCE = 0.25  # mm: section decimation and flat-panel snapping
MAX_SECTIONS = 16  # keeps the ruled loft under the label analysis face budget
ARC_POINTS = 11  # per end arc; each section has 2 * ARC_POINTS + 4 points
EXPONENT_GRID = tuple(2.0 + 0.25 * index for index in range(33))  # 2 .. 10


class SectionShapeClass(StrEnum):
    ROUND = "ROUND"
    OVAL = "OVAL"
    ROUNDED_RECTANGLE = "ROUNDED_RECTANGLE"


class OvalFitRefusal(ValueError):
    """Typed refusal: ``code`` is stable, the message is owner-readable."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class SliceFit:
    """One height band. In the returned (second-pass) slices the half-axes are along and
    across the common orientation (``angle_deg``), not necessarily major >= minor."""

    z: float
    observed: bool
    center: tuple[float, float]
    half_major: float
    half_minor: float
    exponent: float
    angle_deg: float  # major axis direction, Scan Master frame, [0, 180)
    coverage: float
    ellipse_rms: float
    superellipse_rms: float
    points: int

    def as_dict(self) -> dict[str, object]:
        return {
            "z": round(self.z, 4),
            "observed": self.observed,
            "center": [round(v, 4) for v in self.center],
            "half_major": round(self.half_major, 4),
            "half_minor": round(self.half_minor, 4),
            "exponent": round(self.exponent, 3),
            "angle_deg": round(self.angle_deg, 3),
            "coverage": round(self.coverage, 3),
            "ellipse_rms": round(self.ellipse_rms, 4),
            "superellipse_rms": round(self.superellipse_rms, 4),
            "points": self.points,
        }


@dataclass(frozen=True, slots=True)
class DesignSection:
    """One loft section in the design frame (major axis on X): z, centre, half-axes, n."""

    z: float
    cx: float
    cy: float
    a: float
    b: float
    n: float
    zone: str

    def as_list(self) -> list[object]:
        return [
            round(self.z, 4),
            round(self.cx, 4),
            round(self.cy, 4),
            round(self.a, 4),
            round(self.b, 4),
            round(self.n, 4),
            self.zone,
        ]


@dataclass(frozen=True, slots=True)
class OvalSectionFit:
    classification: SectionShapeClass
    orientation_deg: float  # Scan Master major-axis angle; design frame rotates it onto +X
    origin_xy: tuple[float, float]  # Scan Master point that becomes the design-frame axis
    z_base: float
    aspect_ratio: float
    exponent: float
    relative_residual: float
    orientation_spread_deg: float
    tilt_deg: float  # Scan Master z axis to the fitted body axis (re-levelled first)
    level_rotation: tuple[float, ...]  # row-major 3x3, applied to Scan Master points first
    slices: tuple[SliceFit, ...]
    zones: tuple[tuple[str, float, float], ...]
    sections: tuple[DesignSection, ...]
    notes: tuple[str, ...]

    @property
    def width(self) -> float:  # design-frame X extent of the lofted sections
        return max(s.cx + s.a for s in self.sections) - min(s.cx - s.a for s in self.sections)

    @property
    def depth(self) -> float:  # design-frame Y extent
        return max(s.cy + s.b for s in self.sections) - min(s.cy - s.b for s in self.sections)

    @property
    def height(self) -> float:
        return self.sections[-1].z - self.sections[0].z

    @property
    def neck_diameter(self) -> float:
        top = self.sections[-1]
        return top.a + top.b

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.oval-section-fit.v1",
            "method": METHOD,
            "seed": SEED,
            "classification": self.classification.value,
            "orientation_deg": round(self.orientation_deg, 3),
            "tilt_deg": round(self.tilt_deg, 3),
            "scan_master_to_design_frame": {
                "first_rotate_row_major": [round(v, 9) for v in self.level_rotation],
                "translate_xy": [round(-v, 4) for v in self.origin_xy],
                "translate_z": round(-self.z_base, 4),
                "then_rotate_z_deg": round(-self.orientation_deg, 3),
            },
            "aspect_ratio": round(self.aspect_ratio, 4),
            "exponent": round(self.exponent, 3),
            "relative_residual": round(self.relative_residual, 5),
            "orientation_spread_deg": round(self.orientation_spread_deg, 3),
            "thresholds": {
                "round_min_aspect": ROUND_MIN_ASPECT,
                "rectangle_min_exponent": RECTANGLE_MIN_EXPONENT,
                "max_relative_residual": MAX_RELATIVE_RESIDUAL,
                "max_orientation_spread_deg": MAX_ORIENTATION_SPREAD_DEG,
                "level_tolerance_deg": LEVEL_TOLERANCE_DEG,
                "max_tilt_deg": MAX_TILT_DEG,
                "max_tilt_stderr_deg": MAX_TILT_STDERR_DEG,
                "min_slice_coverage": MIN_SLICE_COVERAGE,
                "min_body_slices": MIN_BODY_SLICES,
                "section_tolerance": SECTION_TOLERANCE,
            },
            "overall": {
                "width": round(self.width, 3),
                "depth": round(self.depth, 3),
                "height": round(self.height, 3),
                "neck_diameter": round(self.neck_diameter, 3),
            },
            "zones": [[name, round(z0, 4), round(z1, 4)] for name, z0, z1 in self.zones],
            "slices": [item.as_dict() for item in self.slices],
            "sections": [item.as_list() for item in self.sections],
            "notes": list(self.notes),
            "scale_state": "METRIC_UNVERIFIED",
            "physical_accuracy_validation_status": "DEFERRED_OWNER_VALIDATION",
        }


# ------------------------------------------------------------------ section fits


def _conic(x: np.ndarray, y: np.ndarray) -> np.ndarray | None:
    """Halir-Flusser direct ellipse fit: conic (A..F) or None when degenerate."""
    d1 = np.c_[x * x, x * y, y * y]
    d2 = np.c_[x, y, np.ones_like(x)]
    s1, s2, s3 = d1.T @ d1, d1.T @ d2, d2.T @ d2
    try:
        t = -np.linalg.solve(s3, s2.T)
    except np.linalg.LinAlgError:
        return None
    m = s1 + s2 @ t
    m = np.array([m[2] / 2, -m[1], m[0] / 2])
    if not np.all(np.isfinite(m)):
        return None
    values, vectors = np.linalg.eig(m)
    vectors = np.real(vectors)
    condition = 4 * vectors[0] * vectors[2] - vectors[1] ** 2
    good = np.flatnonzero(condition > 0)
    if len(good) != 1:
        return None
    a1 = vectors[:, good[0]]
    return np.concatenate([a1, t @ a1])


def _sampson(conic: np.ndarray, x: np.ndarray, y: np.ndarray) -> np.ndarray:
    a, b, c, d, e, f = conic
    value = a * x * x + b * x * y + c * y * y + d * x + e * y + f
    gx, gy = 2 * a * x + b * y + d, b * x + 2 * c * y + e
    return np.abs(value) / np.maximum(np.hypot(gx, gy), 1e-12)


def _ellipse_parameters(conic: np.ndarray) -> tuple[float, float, float, float, float] | None:
    """(cx, cy, half_major, half_minor, angle_rad of the major axis) of a conic."""
    a, b, c, d, e, f = conic
    det = 4 * a * c - b * b
    if det <= 0:
        return None
    cx = (b * e - 2 * c * d) / det
    cy = (b * d - 2 * a * e) / det
    value = a * cx * cx + b * cx * cy + c * cy * cy + d * cx + e * cy + f
    eigen, vectors = np.linalg.eigh(np.array([[a, b / 2], [b / 2, c]]))
    if value == 0 or np.any(-value / eigen <= 0):
        return None
    axes = np.sqrt(-value / eigen)
    major = int(np.argmax(axes))
    vector = vectors[:, major]
    return (
        float(cx),
        float(cy),
        float(axes[major]),
        float(axes[1 - major]),
        float(math.atan2(vector[1], vector[0])),
    )


def _robust_ellipse(
    xy: np.ndarray, rng: np.random.Generator
) -> tuple[tuple[float, float, float, float, float], np.ndarray] | None:
    mean = xy.mean(axis=0)
    scale = float(np.sqrt(((xy - mean) ** 2).sum(axis=1).mean())) or 1.0
    unit = (xy - mean) / scale
    x, y = unit[:, 0], unit[:, 1]
    best, best_median = None, math.inf
    probe = rng.choice(len(unit), min(len(unit), 600), replace=False)
    for _ in range(120):  # least median of Sampson distances over 6-point subsets
        pick = rng.choice(len(unit), 6, replace=False)
        conic = _conic(x[pick], y[pick])
        if conic is None or _ellipse_parameters(conic) is None:
            continue
        median = float(np.median(_sampson(conic, x[probe], y[probe])))
        if median < best_median:
            best, best_median = conic, median
    if best is None:
        return None
    inliers = np.ones(len(unit), dtype=bool)
    conic = best
    for _ in range(3):  # trimmed refit
        distance = _sampson(conic, x, y)
        sigma = 1.4826 * float(np.median(distance[inliers]))
        inliers = distance <= max(3.0 * sigma, 0.002)
        if inliers.sum() < 6:
            return None
        refit = _conic(x[inliers], y[inliers])
        if refit is None or _ellipse_parameters(refit) is None:
            break
        conic = refit
    params = _ellipse_parameters(conic)
    if params is None:
        return None
    cx, cy, major, minor, angle = params
    return (cx * scale + mean[0], cy * scale + mean[1], major * scale, minor * scale, angle), (
        inliers
    )


def _superellipse_radius(phi: np.ndarray, a: float, b: float, n: float) -> np.ndarray:
    c = np.maximum(np.abs(np.cos(phi)) / a, 1e-300)
    s = np.maximum(np.abs(np.sin(phi)) / b, 1e-300)
    return np.asarray((c**n + s**n) ** (-1.0 / n))


def _superellipse(
    local: np.ndarray, a0: float, b0: float, exponents: tuple[float, ...] = EXPONENT_GRID
) -> tuple[float, float, float, float]:
    """Best (a, b, n, rms) on the exponent grid; for fixed n the implicit form is linear."""
    rho = np.hypot(local[:, 0], local[:, 1])
    phi = np.arctan2(local[:, 1], local[:, 0])
    u, v = np.abs(local[:, 0]) / a0, np.abs(local[:, 1]) / b0
    best = (a0, b0, 2.0, math.inf)
    for n in exponents:
        design = np.c_[u**n, v**n]
        try:
            coefficients = np.linalg.lstsq(design, np.ones(len(u)), rcond=None)[0]
        except np.linalg.LinAlgError:
            continue
        if np.any(coefficients <= 0):
            continue
        a, b = a0 * coefficients[0] ** (-1 / n), b0 * coefficients[1] ** (-1 / n)
        rms = float(np.sqrt(np.mean((rho - _superellipse_radius(phi, a, b, n)) ** 2)))
        if rms < best[3] - 1e-9:
            best = (float(a), float(b), n, rms)
    return best


def _coverage(xy: np.ndarray, center: tuple[float, float]) -> float:
    angles = np.arctan2(xy[:, 1] - center[1], xy[:, 0] - center[0])
    bins = np.floor((angles + math.pi) / math.tau * 36).astype(int) % 36
    counts = np.bincount(bins, minlength=36)
    return float((counts >= 2).sum() / 36)


def _outer_skin(xy: np.ndarray) -> np.ndarray:
    """Drop points well inside the outer wall (base disc, interior wall seen through the
    opening): per 5-degree bin keep radii within a band below the bin's 90th percentile."""
    centre = np.median(xy, axis=0)
    radius = np.hypot(*(xy - centre).T)
    bins = np.floor((np.arctan2(*(xy - centre).T[::-1]) + math.pi) / math.tau * 72).astype(int)
    keep = np.zeros(len(xy), dtype=bool)
    band = max(1.5, 0.08 * float(np.median(radius)))
    for index in np.unique(bins):
        members = bins == index
        keep |= members & (radius >= np.percentile(radius[members], 90) - band)
    return xy[keep]


def _fit_slice(
    xy: np.ndarray,
    z: float,
    rng: np.random.Generator,
    frame: tuple[tuple[float, float], float] | None = None,
) -> SliceFit:
    """Pass 1 (``frame`` None): free robust ellipse frame. Pass 2: centre and major-axis
    angle fixed to the common frame, so a partial ring (hole) only fits a, b and n."""
    empty = SliceFit(z, False, (0.0, 0.0), 0.0, 0.0, 2.0, 0.0, 0.0, math.inf, math.inf, len(xy))
    if len(xy) < MIN_SLICE_POINTS:
        return empty
    if len(xy) > 4000:
        xy = xy[rng.choice(len(xy), 4000, replace=False)]
    xy = _outer_skin(xy)
    if len(xy) < MIN_SLICE_POINTS:
        return empty
    if frame is None:
        fitted = _robust_ellipse(xy, rng)
        if fitted is None:
            return empty
        (cx, cy, major, minor, angle), _inliers = fitted
        if not 0 < minor <= major <= 2.0 * float(np.ptp(xy, axis=0).max()):
            return empty
    else:
        (cx, cy), angle = frame
    rotation = np.array([[math.cos(angle), math.sin(angle)], [-math.sin(angle), math.cos(angle)]])
    local = (xy - (cx, cy)) @ rotation.T
    rho, phi = np.hypot(local[:, 0], local[:, 1]), np.arctan2(local[:, 1], local[:, 0])
    a0 = max(float(np.percentile(np.abs(local[:, 0]), 95)), 1e-6)
    b0 = max(float(np.percentile(np.abs(local[:, 1]), 95)), 1e-6)
    mask = np.ones(len(local), dtype=bool)
    a, b, n, rms = a0, b0, 2.0, math.inf
    for _ in range(3):  # trimmed superellipse refit on the radial residual
        if mask.sum() < MIN_SLICE_POINTS:
            return empty
        a, b, n, rms = _superellipse(local[mask], a0, b0)
        if not math.isfinite(rms):
            return empty
        residual = rho - _superellipse_radius(phi, a, b, n)
        mad = float(np.median(np.abs(residual[mask])))
        mask = np.abs(residual) <= max(3 * 1.4826 * mad, 0.3)
    ellipse = _superellipse(local[mask], a0, b0, exponents=(2.0,))
    coverage = _coverage(xy[mask], (cx, cy))
    observed = coverage >= MIN_SLICE_COVERAGE and 0 < min(a, b)
    if frame is None and b > a:  # a squarer fit may swap which axis is longer
        a, b, angle = b, a, angle + math.pi / 2
    return SliceFit(
        z,
        observed,
        (float(cx), float(cy)),
        a,
        b,
        n,
        math.degrees(angle) % 180.0,
        coverage,
        ellipse[3],
        min(rms, ellipse[3]),
        int(mask.sum()),
    )


# ------------------------------------------------------------------ along the height


def _orientation(slices: list[SliceFit]) -> tuple[float, float]:
    """Weighted circular mean of the oval slices' major-axis angles and the 90th percentile
    of their deviation (deg). Slices seen nearly all round decide when there are enough."""
    oval = [s for s in slices if s.observed and s.half_minor / s.half_major < ROUND_MIN_ASPECT]
    if not oval:
        return 0.0, 0.0
    full = [s for s in oval if s.coverage >= 0.75]
    oval = full if len(full) >= MIN_BODY_SLICES else oval
    weights = np.array([1 - s.half_minor / s.half_major for s in oval])
    doubled = np.radians([2 * s.angle_deg for s in oval])
    c, s_ = float(np.sum(weights * np.cos(doubled))), float(np.sum(weights * np.sin(doubled)))
    mean = math.degrees(math.atan2(s_, c)) / 2 % 180.0
    deviation = [abs((s.angle_deg - mean + 90.0) % 180.0 - 90.0) for s in oval]
    return mean, float(np.percentile(deviation, 90))


def _median3(values: np.ndarray) -> np.ndarray:
    if len(values) < 3:
        return values.copy()
    padded = np.r_[values[0], values, values[-1]]
    return np.median(np.c_[padded[:-2], padded[1:-1], padded[2:]], axis=1)


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs, start = [], None
    for index, value in enumerate([*mask.tolist(), False]):
        if value and start is None:
            start = index
        elif not value and start is not None:
            runs.append((start, index - 1))
            start = None
    return runs


def _decimate(points: np.ndarray, tolerance: float) -> list[int]:
    """Douglas-Peucker over rows (z, value...) on the max value deviation."""
    keep = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    while stack:
        low, high = stack.pop()
        if high - low < 2:
            continue
        z = points[low + 1 : high, 0]
        t = ((z - points[low, 0]) / (points[high, 0] - points[low, 0]))[:, None]
        line = points[low, 1:] + t * (points[high, 1:] - points[low, 1:])
        errors = np.abs(points[low + 1 : high, 1:] - line).max(axis=1)
        worst = int(np.argmax(errors))
        if errors[worst] > tolerance:
            middle = low + 1 + worst
            keep.add(middle)
            stack.extend(((low, middle), (middle, high)))
    return sorted(keep)


@dataclass(frozen=True, slots=True)
class _FirstPass:
    rng: np.random.Generator
    z0: float
    height: float
    edges: np.ndarray
    zs: np.ndarray
    bands: list[np.ndarray]
    first: list[SliceFit]
    middle: np.ndarray
    trusted: list[SliceFit]


def _axis_drift(trusted: list[SliceFit]) -> tuple[np.ndarray, float, int]:
    """Slope (dx/dz, dy/dz) of the body-prism slice centres, its standard error as an angle
    (deg) and the number of slices used. Only slices whose half-axes match the body median
    (3 %) count, so a shoulder leaning towards an offset neck does not read as tilt."""
    major = float(np.median([s.half_major for s in trusted]))
    minor = float(np.median([s.half_minor for s in trusted]))
    body = [
        s
        for s in trusted
        if abs(s.half_major - major) <= 0.03 * major and abs(s.half_minor - minor) <= 0.03 * major
    ]
    z = np.array([s.z for s in body])
    if len(body) < MIN_BODY_SLICES or float(np.ptp(z)) <= 0:
        return np.zeros(2), math.inf, len(body)
    centres = np.array([s.center for s in body])
    design = np.c_[z - z.mean(), np.ones_like(z)]
    coefficients = np.linalg.lstsq(design, centres, rcond=None)[0]
    residual = centres - design @ coefficients
    sigma = float(np.sqrt(np.sum(residual**2) / (2 * (len(body) - 2))))
    spread = math.sqrt(float(np.sum((z - z.mean()) ** 2)))
    return coefficients[0], math.degrees(math.atan(sigma / spread)), len(body)


def _levelling(slope: np.ndarray) -> np.ndarray:
    """Rotation taking the axis direction (slope_x, slope_y, 1) onto +Z (Rodrigues)."""
    d = np.array([slope[0], slope[1], 1.0])
    d /= np.linalg.norm(d)
    k = np.cross(d, (0.0, 0.0, 1.0))
    s, c = float(np.linalg.norm(k)), float(d[2])
    if s < 1e-12:
        return np.eye(3)
    k /= s
    cross = np.array([[0.0, -k[2], k[1]], [k[2], 0.0, -k[0]], [-k[1], k[0], 0.0]])
    return np.asarray(np.eye(3) + s * cross + (1.0 - c) * cross @ cross)


def fit_oval_sections(
    vertices: np.ndarray,
    *,
    slice_count: int = SLICE_COUNT,
    progress: Callable[[int], None] | None = None,
) -> OvalSectionFit:
    """Fit, classify and zone a scan; refuse with ``OvalFitRefusal`` if neither fits.

    The Scan Master z axis is not trusted blindly: when the body slice centres drift with
    height (a tilted scan) the points are re-levelled about the fitted body axis and fitted
    again, up to ``MAX_TILT_DEG``; a larger or badly determined tilt is refused.
    ``progress`` gets the running count of fitted slices; raising from it cancels the fit.
    """
    points = np.asarray(vertices, dtype=np.float64)
    if points.ndim != 2 or points.shape[1] != 3 or len(points) < MIN_SLICE_POINTS * 4:
        raise OvalFitRefusal("scan_too_small", "the Scan Master has too few points for a fit")
    if not np.all(np.isfinite(points)):
        raise OvalFitRefusal("scan_not_finite", "the Scan Master has non-finite coordinates")
    done = 0

    def tick() -> None:
        nonlocal done
        done += 1
        if progress is not None:
            progress(done)

    rotation = np.eye(3)
    for _ in range(LEVEL_ITERATIONS):
        stage = _first_pass(points @ rotation.T, slice_count, tick)
        slope, stderr, used = _axis_drift(stage.trusted)
        if stderr > MAX_TILT_STDERR_DEG:
            raise OvalFitRefusal(
                "axis_tilt_undetermined",
                f"the body axis direction is not well determined ({used} straight body "
                f"sections, standard error {stderr:.1f} deg > {MAX_TILT_STDERR_DEG:g} deg); "
                "level the Scan Master base or recapture the side",
            )
        if math.degrees(math.atan(float(np.hypot(*slope)))) <= LEVEL_TOLERANCE_DEG:
            break
        rotation = _levelling(slope) @ rotation
        total = math.degrees(math.acos(min(1.0, float(rotation[2, 2]))))
        if total > MAX_TILT_DEG:
            raise OvalFitRefusal(
                "scan_not_upright",
                f"the body axis leans {total:.1f} deg from the Scan Master z axis "
                f"(> {MAX_TILT_DEG:g} deg); level the Scan Master base and fit again",
            )
    else:
        raise OvalFitRefusal(
            "axis_tilt_not_converged",
            f"re-levelling did not settle within {LEVEL_ITERATIONS} passes; level the Scan "
            "Master base and fit again",
        )
    return _finish(stage, rotation, slice_count, tick)


def _first_pass(points: np.ndarray, slice_count: int, tick: Callable[[], None]) -> _FirstPass:
    z0, z1 = (float(v) for v in np.percentile(points[:, 2], [0.05, 99.95]))
    height = z1 - z0
    if height <= 0:
        raise OvalFitRefusal("scan_flat", "the Scan Master has no height")
    rng = np.random.default_rng(SEED)
    edges = np.linspace(z0, z1, slice_count + 1)
    bands = [
        points[(points[:, 2] >= low) & (points[:, 2] <= high), :2]
        for low, high in zip(edges[:-1], edges[1:], strict=True)
    ]
    zs = (edges[:-1] + edges[1:]) / 2
    first = []
    for band, z in zip(bands, zs, strict=True):
        first.append(_fit_slice(band, float(z), rng))
        tick()
    middle = (zs >= z0 + 0.2 * height) & (zs <= z0 + 0.8 * height)
    trusted = [s for s, m in zip(first, middle, strict=True) if s.observed and m]
    if len(trusted) < MIN_BODY_SLICES:
        raise OvalFitRefusal(
            "insufficient_observed_sections",
            f"only {len(trusted)} side sections between 20 and 80 % of the height show >= "
            f"{MIN_SLICE_COVERAGE:.0%} of the circumference (need {MIN_BODY_SLICES}); take "
            "more photos around the side and rebuild",
        )
    return _FirstPass(rng, z0, height, edges, zs, bands, first, middle, trusted)


def _finish(
    stage: _FirstPass, rotation: np.ndarray, slice_count: int, tick: Callable[[], None]
) -> OvalSectionFit:
    rng, z0, height, edges, zs = stage.rng, stage.z0, stage.height, stage.edges, stage.zs
    bands, first, middle, trusted = stage.bands, stage.first, stage.middle, stage.trusted
    tilt_deg = math.degrees(math.acos(min(1.0, float(rotation[2, 2]))))
    orientation, spread = _orientation(trusted)
    axis = (
        float(np.median([s.center[0] for s in trusted])),
        float(np.median([s.center[1] for s in trusted])),
    )
    # Pass 2 in the common frame. A slice keeps its own centre only when it was seen nearly
    # all round (an offset neck); partial rings use the body axis.
    slices = []
    for band, z, item in zip(bands, zs, first, strict=True):
        centre = item.center if item.observed and item.coverage >= 0.75 else axis
        slices.append(_fit_slice(band, float(z), rng, (centre, math.radians(orientation))))
        tick()
    observed = np.array([s.observed for s in slices])
    if int((observed & middle).sum()) < MIN_BODY_SLICES:
        raise OvalFitRefusal(
            "insufficient_observed_sections",
            f"only {int((observed & middle).sum())} side sections between 20 and 80 % of the "
            f"height fit the common oval frame (need {MIN_BODY_SLICES}); recapture the side",
        )
    table = np.zeros((slice_count, 6))  # cx, cy, a (along orientation), b, n, rms
    for index, item in enumerate(slices):
        if item.observed:
            table[index] = (
                *item.center,
                item.half_major,
                item.half_minor,
                item.exponent,
                item.superellipse_rms,
            )
    # Interpolate holes inside the observed height only; ends take the nearest observed.
    known = np.flatnonzero(observed)
    for column in range(5):
        table[known, column] = _median3(table[known, column])
        table[:, column] = np.interp(zs, zs[known], table[known, column])
    body_slices = observed & middle
    a_med = float(np.median(table[body_slices, 2]))
    b_med = float(np.median(table[body_slices, 3]))
    n_med = float(np.median(table[body_slices, 4]))
    aspect = min(a_med, b_med) / max(a_med, b_med)
    residual = float(np.median(table[body_slices, 5] / table[body_slices, 2]))
    if residual > MAX_RELATIVE_RESIDUAL:
        raise OvalFitRefusal(
            "section_not_round_or_oval",
            f"the side sections are neither round nor oval: residual {residual:.1%} of the "
            f"half-width > {MAX_RELATIVE_RESIDUAL:.0%} (handles, ribs, a dent or a noisy scan)",
        )
    if aspect < ROUND_MIN_ASPECT and spread > MAX_ORIENTATION_SPREAD_DEG:
        raise OvalFitRefusal(
            "orientation_inconsistent",
            f"the oval sections twist along the height (spread {spread:.1f} deg > "
            f"{MAX_ORIENTATION_SPREAD_DEG:g} deg); not one oval body",
        )
    if n_med >= RECTANGLE_MIN_EXPONENT:
        classification = SectionShapeClass.ROUNDED_RECTANGLE
    elif aspect >= ROUND_MIN_ASPECT:
        classification = SectionShapeClass.ROUND
    else:
        classification = SectionShapeClass.OVAL
    if classification is not SectionShapeClass.ROUNDED_RECTANGLE:
        table[:, 4] = 2.0  # ellipse (or circle) model: exponent fixed
    # Zones from the smoothed half-axes.
    tol_a, tol_b = max(0.6, 0.02 * a_med), max(0.6, 0.02 * b_med)
    in_body = (np.abs(table[:, 2] - a_med) <= tol_a) & (np.abs(table[:, 3] - b_med) <= tol_b)
    seed = int(np.flatnonzero(middle)[np.argmin(np.abs(table[middle, 2] - a_med))])
    body = next(((lo, hi) for lo, hi in _runs(in_body) if lo <= seed <= hi), (seed, seed))
    top_size = table[-1, 2] + table[-1, 3]
    neck_start = slice_count
    if top_size < 0.8 * (a_med + b_med):
        neck_start = slice_count - 1
        while neck_start - 1 > body[1] and abs(
            table[neck_start - 1, 2] + table[neck_start - 1, 3] - top_size
        ) <= max(0.6, 0.04 * top_size):
            neck_start -= 1
    zone_names = []
    for index in range(slice_count):
        if index < body[0]:
            zone_names.append("base")
        elif index <= body[1]:
            zone_names.append("body")
        elif index < neck_start:
            zone_names.append("shoulder")
        else:
            zone_names.append("neck")
    # The body is one straight prism (equal sections give planar front/back label panels).
    body_rows = slice(body[0], body[1] + 1)
    table[body_rows, 0:2] = table[body_rows, 0:2].mean(axis=0)
    table[body_rows, 2:5] = (a_med, b_med, float(np.median(table[body_slices, 4])))
    zone_edges = []
    for name in ("base", "body", "shoulder", "neck"):
        indices = [i for i, zone in enumerate(zone_names) if zone == name]
        if indices:
            zone_edges.append((name, float(edges[indices[0]]), float(edges[indices[-1] + 1])))
    # Design frame: axis through the body centre, major axis on +X, base at z = 0.
    origin = (float(table[body[0], 0]), float(table[body[0], 1]))
    theta = math.radians(orientation)
    cos_t, sin_t = math.cos(theta), math.sin(theta)
    dx, dy = table[:, 0] - origin[0], table[:, 1] - origin[1]
    rows = np.c_[
        np.r_[0.0, zs - z0, height],
        np.r_[0.0, dx * cos_t + dy * sin_t, 0.0],
        np.r_[0.0, -dx * sin_t + dy * cos_t, 0.0],
        np.r_[table[0, 2], table[:, 2], table[-1, 2]],
        np.r_[table[0, 3], table[:, 3], table[-1, 3]],
        np.r_[table[0, 4], table[:, 4], table[-1, 4]],
    ]
    rows[0, 1:3], rows[-1, 1:3] = rows[1, 1:3], rows[-2, 1:3]
    names = [zone_names[0], *zone_names, zone_names[-1]]
    tolerance = SECTION_TOLERANCE
    while True:  # an exponent change of 1 counts like 0.25 mm of the half-axes
        keep = _decimate(np.c_[rows[:, :5], rows[:, 5] * 0.25], tolerance)
        if len(keep) <= MAX_SECTIONS:
            break
        tolerance *= 1.5
    sections = tuple(
        DesignSection(
            float(rows[i, 0]),
            float(rows[i, 1]),
            float(rows[i, 2]),
            float(rows[i, 3]),
            float(rows[i, 4]),
            float(rows[i, 5]),
            names[i],
        )
        for i in keep
    )
    notes = (
        [
            f"{int((~observed).sum())} of {slice_count} height slices had too little of the "
            "circumference observed and were interpolated from their neighbours",
        ]
        if (~observed).any()
        else []
    )
    if tolerance > SECTION_TOLERANCE:
        notes.append(f"section decimation tolerance raised to {tolerance:.2f} mm")
    if tilt_deg > 0.0:
        notes.append(
            f"the body axis leaned {tilt_deg:.2f} deg from the Scan Master z axis; the points "
            "were re-levelled about the fitted axis first (scan_master_to_design_frame)"
        )
    return OvalSectionFit(
        classification,
        orientation,
        origin,
        z0,
        aspect,
        n_med if classification is SectionShapeClass.ROUNDED_RECTANGLE else 2.0,
        residual,
        spread,
        tilt_deg,
        tuple(float(v) for v in rotation.ravel()),
        tuple(slices),
        tuple(zone_edges),
        sections,
        tuple(notes),
    )


def section_outline(
    a: float, b: float, n: float, cx: float = 0.0, cy: float = 0.0
) -> tuple[tuple[float, float], ...]:
    """Counter-clockwise section polygon with straight front (+Y) and back (-Y) panels.

    The panel spans the part of the superellipse within ``SECTION_TOLERANCE`` of ``y = b``,
    so a ruled loft of equal sections has one planar face facing +/-Y (label host); the
    point count is fixed (``2 * ARC_POINTS + 4``) so every section of a model is compatible.
    """
    if not (a > 0 and b > 0 and n >= 1.0):
        raise ValueError("section_half_axes_invalid")
    ratio = 1.0 - min(SECTION_TOLERANCE / b, 0.5)
    panel = a * (1.0 - ratio**n) ** (1.0 / n)
    t_panel = math.acos(min((panel / a) ** (n / 2.0), 1.0))

    def point(t: float) -> tuple[float, float]:
        c, s = math.cos(t), math.sin(t)
        return (
            cx + a * math.copysign(abs(c) ** (2.0 / n), c),
            cy + b * math.copysign(abs(s) ** (2.0 / n), s),
        )

    def arc(centre: float) -> list[tuple[float, float]]:
        step = 2 * t_panel / (ARC_POINTS + 1)
        return [point(centre - t_panel + step * k) for k in range(1, ARC_POINTS + 1)]

    outline = [(cx + panel, cy + b), (cx - panel, cy + b)]
    outline += arc(math.pi)
    outline += [(cx - panel, cy - b), (cx + panel, cy - b)]
    outline += arc(0.0)
    return tuple(outline)


__all__ = [
    "DesignSection",
    "OvalFitRefusal",
    "OvalSectionFit",
    "SectionShapeClass",
    "SliceFit",
    "fit_oval_sections",
    "section_outline",
]
