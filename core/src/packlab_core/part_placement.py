"""Place the closure on the body using the assembled scan as reference (PL-0484).

Inputs are three parts in their own A4-mat frames (mm, +z up from the mat, object points only),
e.g. merged clouds from ``multiscan_alignment.align_part_pair`` or a single scan through
``part_from_scan``. Both parts are registered into the assembled cloud with the PL-0483 tools:

* Heights first: the closure top sits on the assembled top, so the closure skirt starts at
  ``cut = H_assembled - H_closure``; the body below ``cut`` is the only part of the body the
  assembled scan can see (the closure hides the neck). Typed refusal when the heights cannot
  belong to one seated assembly (closure floating above the body, assembled lower than body).
* Body: outer wall below ``cut`` vs the assembled wall below ``cut``; height from the shared
  mat contact; yaw sweep + in-plane ICP, bounded tilt refine (``_pose_for_flip``).
* Closure: outer wall vs the assembled wall above ``cut``; height from top contact, same pose
  search.

Acceptance per part (like ``multiscan_alignment``): bidirectional diameter-profile check over
the shared height bands, worst-slice coverage, RMSE, free-space conflict (placed points above
what the assembled scan saw), yaw only when the wall profile pins it or both walls are round.
Seat check: the skirt bottom the assembled scan shows (lowest height where its near-vertical wall
still sits on the closure's outer radius) must match ``cut``; a lid of the wrong height (or a
flush lid whose seam is not visible) is refused. Gross interference (closure points inside the
placed body wall, e.g. an upside-down lid or a too-tall neck) is refused; small overlaps stay a
CANDIDATE_OVERLAP flag. A lid seated cocked in the assembled scan is refused (free-space
conflict / seat mismatch): seat it straight and rescan.
Refusals raise ``PartPlacementError`` with typed ``codes``. Sizes scale with the measured point
spacing. Deterministic. Metric values stay METRIC_UNVERIFIED; tests use synthetic proxies only.

The scan-level assembly graph reuses the existing assembly API types (``AssemblyComponentRole``,
``AssemblyComponentPlacement``, ``PairClearanceDiagnostic``); ``create_parametric_assembly_graph``
itself needs Design Model revisions for all four roles, which scanned parts do not have yet.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, replace

import numpy as np

from .assembly_clearance import (
    AssemblyComponentPlacement,
    PairClearanceDiagnostic,
    PairDiagnosticStatus,
    _box_distance,
)
from .assembly_graph import AssemblyComponentRole, AssemblyRelationshipKind
from .multiscan_alignment import (
    AlignmentThresholds,
    MultiScanAlignmentError,
    Query,
    ScanInput,
    _adapt,
    _apply,
    _centre,
    _free_space_conflict,
    _is_round,
    _nearest,
    _normals,
    _Part,
    _Pose,
    _pose_for_flip,
    _prepare,
    _shell,
    _spacing,
    _top,
    _voxel_first,
    _width,
    _yaw_unique,
)

METHOD = "assembled_reference_cut_height_yaw_sweep_bounded_tilt_icp_v1"
METRIC_STATUS = "METRIC_UNVERIFIED"
GRAPH_CONTRACT = "packlab.scan-part-assembly-graph.v1"
PROFILE_BANDS = 6
MAX_INTERFERENCE_SHARE = 0.05  # refused above: not a thread engagement
CANDIDATE_INTERFERENCE_SHARE = 0.01  # flagged CANDIDATE_OVERLAP above
_DEFERRED = "DEFERRED_OWNER_VALIDATION"


class PartPlacementError(ValueError):
    """Placement refused; ``codes`` names every failed check (message has the details)."""

    def __init__(self, message: str, codes: tuple[str, ...]) -> None:
        super().__init__(message)
        self.codes = codes


@dataclass(frozen=True)
class PartInput:
    part_id: str
    points: np.ndarray  # (N, 3) object points in the part's own mat frame, mm, z up
    colors: np.ndarray | None = None  # (N, 3) in [0, 1]


@dataclass(frozen=True)
class PartPlacement:
    part_id: str
    role: str  # "body" | "closure"
    matrix: np.ndarray  # 4x4 rigid: part mat frame mm -> assembled mat frame mm
    coverage: float  # worst wall slice, both directions
    rmse_mm: float
    yaw_determined: bool  # False only when both walls are round (yaw arbitrary)
    yaw_uncertainty_deg: float
    free_space_conflict: float
    dof: str


@dataclass(frozen=True)
class ClosurePlacement:
    assembled_id: str
    body: PartPlacement
    closure: PartPlacement
    closure_on_body: np.ndarray  # 4x4 rigid: closure frame -> body frame
    heights_mm: dict[str, float]  # assembled / body / closure
    engaged_depth_mm: float  # body height hidden inside the closure (H_b + H_c - H_a)
    observed_seat_mm: float  # skirt bottom seen in the assembled scan (expected: H_a - H_c)
    interference_point_share: float  # closure points inside the body wall beyond tolerance
    interference_depth_mm: float  # 95th percentile penetration of those points (0 if none)
    clearance: PairClearanceDiagnostic  # radial closure-to-body wall estimate, candidate only
    aabb_clearance_mm: float
    aabb_overlap_mm: float
    method: str = METHOD
    metric_status: str = METRIC_STATUS


# ---------------------------------------------------------------- inputs


def part_from_scan(
    scan: ScanInput, limits: AlignmentThresholds = AlignmentThresholds()
) -> PartInput:
    """Single (not combined) scan -> object points in its mat frame, mm (PL-0483 preparation)."""

    try:
        part = _prepare(scan, limits)
    except MultiScanAlignmentError as error:
        raise PartPlacementError(str(error), ("part_unusable",)) from None
    colors = None if scan.colors is None else np.asarray(scan.colors)[part.index]
    return PartInput(scan.scan_id, part.points, colors)


def _part(item: PartInput | None, role: str, limits: AlignmentThresholds) -> _Part:
    if item is None:
        raise PartPlacementError(f"{role} part missing", ("part_missing",))
    points = np.asarray(item.points, dtype=float)
    if points.ndim != 2 or points.shape[1:] != (3,) or len(points) < 100:
        raise PartPlacementError(f"{role} part needs (N>=100, 3) points", ("part_unusable",))
    if not np.isfinite(points).all():
        raise PartPlacementError(f"{role} part has non-finite points", ("part_unusable",))
    spacing = _spacing(points, limits.voxel_mm)[0]
    height = _top(points[:, 2])
    try:
        shell, normals = _shell(points, height, spacing, limits)
    except MultiScanAlignmentError as error:
        raise PartPlacementError(f"{role} part: {error}", ("part_unusable",)) from None
    keep = _outermost(shell, points, spacing, limits.voxel_mm)
    if keep.sum() < 30:
        raise PartPlacementError(f"{role} part: too little outer wall", ("part_unusable",))
    return _Part(
        item.part_id,
        np.eye(4),
        points,
        np.arange(len(points)),
        height,
        shell[keep],
        normals[keep],
        spacing,
    )


def _outermost(shell: np.ndarray, points: np.ndarray, spacing: float, voxel: float) -> np.ndarray:
    """Mask of shell points on the outer skin only: a merged part also holds the inner wall
    (closure skirt inside, seen upside down) within ``_shell``'s 2.5 mm, which the assembled
    scan never sees. Keep a shell point when no part point within ~4 spacings lies further out
    than the tolerance (radius about the shell centre)."""

    centre = _centre(shell)
    sample = points[_voxel_first(points, voxel)]
    found, distance = _nearest(sample)(shell, min(32, len(sample)))
    outward = np.linalg.norm(sample[:, :2] - centre, axis=1)[found]
    outer = np.where(distance < max(3.0, 4.0 * spacing), outward, -np.inf).max(axis=1)
    radius = np.linalg.norm(shell[:, :2] - centre, axis=1)
    return np.asarray(radius >= outer - max(0.75, 0.75 * spacing))


def _crop(part: _Part, low: float, high: float, what: str) -> _Part:
    keep = (part.shell[:, 2] > low) & (part.shell[:, 2] < high)
    if keep.sum() < 30:
        raise PartPlacementError(f"too little {what}", ("too_little_wall",))
    return replace(part, shell=part.shell[keep], normals=part.normals[keep])


def _shifted(part: _Part, dz: float) -> _Part:
    shift = np.array([0.0, 0.0, dz])
    return replace(
        part, points=part.points + shift, shell=part.shell + shift, height=part.height + dz
    )


# ---------------------------------------------------------------- checks


def _profile_failures(
    role: str, reference: _Part, other: _Part, low: float, high: float, limits: AlignmentThresholds
) -> list[tuple[str, str]]:
    """Diameter bands between ``low`` and ``high`` (assembled frame, ``other`` already shifted)."""

    half = max(2.0, limits.slice_mm / 2.5)
    lower, upper = low + half, high - half
    heights = (
        np.linspace(lower, upper, PROFILE_BANDS) if upper > lower else np.full(1, (low + high) / 2)
    )
    failures: list[tuple[str, str]] = []
    valid = seen_ref = seen_other = 0
    for z in heights:
        mine, theirs = _width(reference.shell, z, half), _width(other.shell, z, half)
        seen_ref += int(not np.isnan(mine))
        seen_other += int(not np.isnan(theirs))
        if np.isnan(mine) or np.isnan(theirs):
            continue
        valid += 1
        tolerance = max(limits.width_tolerance_mm, limits.dimension_tolerance_ratio * mine)
        tolerance += 0.5 * limits.spacing_mm
        if abs(mine - theirs) > tolerance:
            failures.append(
                (
                    "diameter_mismatch",
                    f"{role} diameter at z={z:.0f} mm: {theirs:.1f} vs assembled {mine:.1f} mm "
                    f"(tolerance {tolerance:.1f})",
                )
            )
    needed = max(1, int(np.ceil(limits.min_profile_share * max(seen_ref, seen_other))))
    if valid < needed:
        failures.append(
            (
                "too_little_wall",
                f"{role}: too little overlapping wall ({valid} of {len(heights)} diameter bands, "
                f"need {needed})",
            )
        )
    return failures


def _fit(
    role: str,
    reference: _Part,
    full_reference: _Part,
    part: _Part,
    full_part: _Part,
    band: tuple[float, float],
    limits: AlignmentThresholds,
) -> tuple[PartPlacement, list[tuple[str, str]]]:
    query: Query = _nearest(reference.shell)
    pose: _Pose = _pose_for_flip(part, reference, query, False, limits)
    moved = replace(part, shell=_apply(pose.matrix, part.shell))  # diameters in assembled frame
    failures = _profile_failures(role, reference, moved, *band, limits)
    cell = max(3.0, 1.5 * limits.max_distance_mm)
    conflict = _free_space_conflict(full_part, full_reference, pose.matrix, cell)
    if conflict > limits.max_free_space_conflict:
        failures.append(
            (
                "free_space_conflict",
                f"{role} free-space conflict {conflict:.3g} > {limits.max_free_space_conflict} "
                "(placed surfaces where the assembled scan saw empty space; if the lid sits "
                "cocked in the assembled scan, seat it straight and rescan)",
            )
        )
    if pose.coverage < limits.min_slice_coverage:
        failures.append(
            ("coverage", f"{role} wall coverage {pose.coverage:.3g} < {limits.min_slice_coverage}")
        )
    if pose.rmse > limits.max_rmse_mm:
        failures.append(("rmse", f"{role} rmse_mm {pose.rmse:.3g} > {limits.max_rmse_mm}"))
    determined = bool(
        pose.yaw_uncertainty <= limits.yaw_probe_deg
        and _yaw_unique(reference, part, pose.matrix, limits)
    )
    if not determined and not (_is_round(reference, limits) and _is_round(part, limits)):
        failures.append(("yaw_undetermined", f"{role} yaw undetermined on a non-symmetric wall"))
    dof = f"tilt_yaw_xy_bounded_refine_height_from_{'mat' if role == 'body' else 'top'}_contact"
    placement = PartPlacement(
        part.scan_id,
        role,
        pose.matrix,
        pose.coverage,
        pose.rmse,
        determined,
        pose.yaw_uncertainty,
        conflict,
        dof,
    )
    return placement, failures


def _radial_clearance(
    body: _Part, closure_points: np.ndarray, limits: AlignmentThresholds
) -> tuple[float, float, float | None]:
    """(share of closure points inside the body's outer wall beyond tolerance, their 95th
    percentile penetration depth mm, 5th percentile radial gap mm) over (height band, 10 degree)
    cells where the placed body wall exists.

    ponytail: radial about the body axis, so only round-ish necks; thread engagement within the
    tolerance reads as clearance. Upgrade: signed distance to the meshed body surface."""

    centre = _centre(body.shell)
    band = max(1.0, 1.5 * body.spacing)

    def cells(points: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        rel = points[:, :2] - centre
        azimuth = ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * 36).astype(int) % 36
        return np.floor(points[:, 2] / band).astype(np.int64) * 36 + azimuth, np.linalg.norm(
            rel, axis=1
        )

    body_keys, body_radius = cells(body.shell)
    keys, inverse = np.unique(body_keys, return_inverse=True)
    outer = np.array([np.median(body_radius[inverse.ravel() == k]) for k in range(len(keys))])
    closure_keys, closure_radius = cells(closure_points)
    slot = np.clip(np.searchsorted(keys, closure_keys), 0, len(keys) - 1)
    hit = keys[slot] == closure_keys
    if not hit.any():
        return 0.0, 0.0, None
    gap = closure_radius[hit] - outer[slot[hit]]
    tolerance = max(limits.width_tolerance_mm, 0.5 * limits.spacing_mm) + 0.5 * limits.spacing_mm
    inside = gap < -tolerance
    depth = float(np.percentile(-gap[inside], 95)) if inside.any() else 0.0
    return float(inside.mean()), depth, float(np.percentile(gap, 5))


def _observed_seat(
    assembled: _Part, closure_shell: np.ndarray, start: float, limits: AlignmentThresholds
) -> float:
    """Lowest height of the contiguous run (walking down from ``start``) of bands where the
    assembled scan's near-vertical surfaces cover at least half of 36 sectors at the placed
    closure's outer radius. Shoulders and rims (horizontal normals excluded) do not count."""

    centre = _centre(closure_shell)
    radius = float(np.median(np.linalg.norm(closure_shell[:, :2] - centre, axis=1)))
    sample = assembled.points[_voxel_first(assembled.points, limits.voxel_mm)]
    wall = sample[np.abs(_normals(sample)[:, 2]) < 0.5]
    rel = wall[:, :2] - centre
    tolerance = max(limits.width_tolerance_mm, limits.dimension_tolerance_ratio * radius)
    on = np.abs(np.linalg.norm(rel, axis=1) - radius) < tolerance + 0.5 * limits.spacing_mm
    sector = ((np.arctan2(rel[:, 1], rel[:, 0]) + np.pi) / (2 * np.pi) * 36).astype(int) % 36
    step = max(0.5, 0.5 * limits.spacing_mm)
    z = start
    while z - step > 0:
        band = on & (wall[:, 2] >= z - step) & (wall[:, 2] < z)
        if len(np.unique(sector[band])) < 18:
            break
        z -= step
    return z


def _bounds(points: np.ndarray) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
    low, high = np.percentile(points, [1, 99], axis=0)
    return (
        (float(low[0]), float(low[1]), float(low[2])),
        (float(high[0]), float(high[1]), float(high[2])),
    )


# ---------------------------------------------------------------- public API


def place_closure_on_body(
    assembled: PartInput | None,
    body: PartInput | None,
    closure: PartInput | None,
    limits: AlignmentThresholds = AlignmentThresholds(),
) -> ClosurePlacement:
    """Register body and closure into the assembled cloud; refuse with typed codes."""

    missing = [
        name
        for name, item in (("assembled", assembled), ("body", body), ("closure", closure))
        if item is None
    ]
    if missing:
        raise PartPlacementError(
            "cannot place the closure: missing " + ", ".join(missing), ("part_missing",)
        )
    a, b, c = (
        _part(item, role, limits)
        for item, role in ((assembled, "assembled"), (body, "body"), (closure, "closure"))
    )
    limits = _adapt(limits, max(a.spacing, b.spacing, c.spacing))
    tolerance = max(limits.height_tolerance_mm, limits.dimension_tolerance_ratio * a.height)
    tolerance += 0.5 * limits.spacing_mm
    engaged = b.height + c.height - a.height
    failures: list[tuple[str, str]] = []
    if engaged < -tolerance:
        failures.append(
            (
                "height_inconsistent",
                f"assembled height {a.height:.1f} mm exceeds body {b.height:.1f} + closure "
                f"{c.height:.1f} mm by {-engaged:.1f} (closure not seated or wrong part)",
            )
        )
    if a.height < b.height + max(1.0, 0.5 * limits.spacing_mm) - tolerance:
        failures.append(
            (
                "height_inconsistent",
                f"assembled height {a.height:.1f} mm is not above the body {b.height:.1f} mm "
                "(wrong body or the assembled scan has no closure)",
            )
        )
    if failures:
        raise PartPlacementError(
            "; ".join(m for _, m in failures), tuple(dict.fromkeys(k for k, _ in failures))
        )
    cut = a.height - c.height  # closure skirt bottom in the assembled frame
    gap = max(2.0, 1.5 * limits.spacing_mm)
    a_low = _crop(a, -np.inf, cut - gap, "assembled wall below the closure")
    a_top = _crop(a, cut + gap / 2, np.inf, "closure wall in the assembled scan")
    b_low = _crop(b, -np.inf, cut - gap, "body wall below the closure")
    c_placed = _shifted(c, cut)
    floor = limits.mat_margin_mm + 2
    body_fit, body_failures = _fit("body", a_low, a, b_low, b, (floor, cut - gap), limits)
    closure_fit, closure_failures = _fit(
        "closure", a_top, a, c_placed, c_placed, (cut + gap / 2, a.height - 2), limits
    )
    failures = body_failures + closure_failures
    if failures:
        raise PartPlacementError(
            "closure placement refused: " + "; ".join(m for _, m in failures),
            tuple(dict.fromkeys(k for k, _ in failures)),
        )
    shift = np.eye(4)
    shift[2, 3] = cut
    closure_fit = replace(closure_fit, matrix=closure_fit.matrix @ shift)
    placed_body = replace(
        b, points=_apply(body_fit.matrix, b.points), shell=_apply(body_fit.matrix, b.shell)
    )
    placed_closure = _apply(closure_fit.matrix, c.points)
    seat = _observed_seat(a, _apply(closure_fit.matrix, c.shell), cut + gap, limits)
    seat_tolerance = max(1.5, 2.0 * limits.spacing_mm)
    interference, depth, radial = _radial_clearance(placed_body, placed_closure, limits)
    failures = []
    if abs(seat - cut) > seat_tolerance:
        failures.append(
            (
                "seat_mismatch",
                f"closure skirt bottom seen at z={seat:.1f} mm in the assembled scan, placed at "
                f"{cut:.1f} mm (tolerance {seat_tolerance:.1f}; engaged depth {engaged:.1f} vs "
                f"seen {b.height - seat:.1f} mm): wrong closure height, flush seam not visible, "
                "or lid not seated straight - seat it straight and rescan",
            )
        )
    if interference > MAX_INTERFERENCE_SHARE:
        failures.append(
            (
                "interference",
                f"closure intersects the body: {interference:.0%} of closure points up to "
                f"{depth:.1f} mm inside the body wall (> {MAX_INTERFERENCE_SHARE:.0%}): wrong "
                "part, upside-down closure or wrong body",
            )
        )
    if failures:
        raise PartPlacementError(
            "closure placement refused: " + "; ".join(m for _, m in failures),
            tuple(k for k, _ in failures),
        )
    if radial is None:
        status = PairDiagnosticStatus.UNKNOWN_PROXY_UNSUPPORTED
    elif interference > CANDIDATE_INTERFERENCE_SHARE:
        status = PairDiagnosticStatus.CANDIDATE_OVERLAP
    elif radial <= limits.width_tolerance_mm:
        status = PairDiagnosticStatus.NEAR_CLEARANCE
    else:
        status = PairDiagnosticStatus.CLEARANCE
    clearance = PairClearanceDiagnostic(
        AssemblyComponentRole.BODY,
        AssemblyComponentRole.CLOSURE,
        status,
        radial,
        depth if depth > 0 else None,  # mm, as in assembly_clearance
        "SCAN_POINT_RADIAL_WALL_GAP_P5_ESTIMATE",
        (AssemblyComponentRole.BODY, AssemblyComponentRole.CLOSURE) if radial is None else (),
    )
    aabb_clearance, aabb_overlap = _box_distance(
        _bounds(placed_body.points), _bounds(placed_closure)
    )
    return ClosurePlacement(
        a.scan_id,
        body_fit,
        closure_fit,
        np.linalg.inv(body_fit.matrix) @ closure_fit.matrix,
        {"assembled": a.height, "body": b.height, "closure": c.height},
        float(engaged),
        float(seat),
        interference,
        depth,
        clearance,
        float(aabb_clearance),
        float(aabb_overlap),
    )


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def _num(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None  # e.g. yaw uncertainty not measured


def _matrix(matrix: np.ndarray) -> tuple[float, ...]:
    return tuple(float(v) for v in np.asarray(matrix, dtype=float).ravel())


def scan_assembly_graph(
    result: ClosurePlacement,
    sources: Mapping[str, Mapping[str, object]],
    reason: str,
    outputs: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Container + closure graph with placements and diagnostics; ``sources`` maps
    assembled/body/closure to JSON provenance (cloud path, sha256, scale source...).

    The revision id hashes the content (not the time), so re-running on the same inputs gives the
    same revision."""

    if set(sources) != {"assembled", "body", "closure"}:
        raise PartPlacementError(
            "graph needs assembled, body and closure sources", ("part_missing",)
        )
    components = []
    for role, placement, assembly_role in (
        ("container", result.body, AssemblyComponentRole.BODY),
        ("closure", result.closure, AssemblyComponentRole.CLOSURE),
    ):
        source = dict(sources["body" if role == "container" else "closure"])
        pin = AssemblyComponentPlacement(
            assembly_role,
            "scan-part:" + _digest(source)[:40],
            role,
            "scan-placement:" + _digest([_matrix(placement.matrix), source])[:40],
            _matrix(placement.matrix),
        )
        components.append(
            {
                "role": role,
                "assembly_role": assembly_role.value,
                "source": source,
                "placed_output": dict((outputs or {}).get(assembly_role.value, {})),
                "placement": pin.as_dict(),
                "residuals": {
                    "coverage": _num(placement.coverage),
                    "rmse_mm": _num(placement.rmse_mm),
                    "yaw_determined": placement.yaw_determined,
                    "yaw_uncertainty_deg": _num(placement.yaw_uncertainty_deg),
                    "free_space_conflict": _num(placement.free_space_conflict),
                    "dof": placement.dof,
                },
            }
        )
    identity: dict[str, object] = {
        "contract": GRAPH_CONTRACT,
        "method": result.method,
        "assembled_source": dict(sources["assembled"]),
        "components": components,
        "relationships": [
            {
                "relationship_id": "assembly-reference:body_to_closure",
                "kind": AssemblyRelationshipKind.BODY_TO_CLOSURE.value,
                "source_role": "container",
                "target_role": "closure",
                "closure_on_body": list(_matrix(result.closure_on_body)),
                "engaged_depth_mm": result.engaged_depth_mm,
            }
        ],
        "diagnostics": {
            "heights_mm": dict(result.heights_mm),
            "observed_seat_mm": result.observed_seat_mm,
            "interference_point_share": result.interference_point_share,
            "interference_depth_mm": result.interference_depth_mm,
            "pair": result.clearance.as_dict(),
            "aabb_clearance_mm": result.aabb_clearance_mm,
            "aabb_overlap_mm": result.aabb_overlap_mm,
        },
        "scale_state": "metric-unverified",
        "coordinate_unit": "mm_unverified",
        "metric_status": result.metric_status,
        "physical_accuracy_validation_status": _DEFERRED,
        "mold_use_authorized": False,
        "certified_fit_claimed": False,
        "authority_class": "SCAN_PART_ASSEMBLY_METADATA",
        "geometry_embedded": False,
        "reason": reason,
    }
    return {"revision_id": "scan-assembly-graph:" + _digest(identity), **identity}


__all__ = [
    "METHOD",
    "METRIC_STATUS",
    "ClosurePlacement",
    "PartInput",
    "PartPlacement",
    "PartPlacementError",
    "part_from_scan",
    "place_closure_on_body",
    "scan_assembly_graph",
]
