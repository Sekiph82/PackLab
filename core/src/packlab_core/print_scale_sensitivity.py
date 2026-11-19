"""PL-0223 calibration-mat print-scale sensitivity (simulation proxy, not physical evidence).

A printed mat whose markers are physically ``s`` times their nominal size makes the real
scale estimators return a factor that is wrong by ``1 / s``: the software assumes the
nominal 40 mm side. This module injects known print-scale errors into synthetic marker
observations, runs them through the real ``estimate_scale`` (image mm/px) and
``estimate_reconstruction_scale`` (3D mm/unit) code paths, and reports the resulting
metric-scale error and its propagation to known object dimensions.

Synthetic ground truth here only verifies the software math. A uniform print error is
self-consistent in camera data and cannot be detected from images; only an owner ruler
measurement of the printed mat can catch it, so that reading is a required owner input
before any physical claim. Nothing here can produce a physical PASS.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import xml.etree.ElementTree as ET
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from .calibration.marker_association import AssociatedMarkerObservation
from .calibration.reconstruction_scale import (
    PhysicalMarkerReference,
    ReconstructedMarkerGeometry,
    ReconstructionScaleObservation,
    estimate_reconstruction_scale,
)
from .calibration.scale_estimation import KnownMarkerObservation, estimate_scale

REPORT_CONTRACT = "packlab.print-scale-sensitivity-report.v1"
REPORT_VERSION = "print_scale_sensitivity_v1"
PHYSICAL_EVIDENCE_PENDING = "PHYSICAL_EVIDENCE_PENDING"
# Provisional print-geometry gate copied from docs/calibration/pre-use-verification.md.
DEFAULT_SPACING_TOLERANCE_MM = 1.0
DEFAULT_MARKER_SIDE_TOLERANCE_MM = 0.5
_SVG = "{http://www.w3.org/2000/svg}"
_RECONSTRUCTION_REVISION = "synthetic-print-scale-reconstruction-r1"
_CAMERA_REVISION = "synthetic-print-scale-camera-r1"


class PrintScaleSensitivityError(ValueError):
    """Raised when mat geometry, scenarios or owner readings are unusable."""


@dataclass(frozen=True, slots=True)
class CalibrationMatProfile:
    """Nominal mat geometry read from the versioned SVG source (not a physical measurement)."""

    mat_id: str
    source_version: str
    source_sha256: str
    page_width_mm: float
    page_height_mm: float
    marker_side_mm: float
    reference_distance_x_mm: float
    reference_distance_y_mm: float
    marker_origins_mm: tuple[tuple[int, float, float], ...]

    def spacing_pairs(self) -> tuple[tuple[str, int, int, float], ...]:
        """Same-row (x) and same-column (y) marker pairs with nominal centre distance."""

        pairs: list[tuple[str, int, int, float]] = []
        for index, (first, fx, fy) in enumerate(self.marker_origins_mm):
            for second, sx, sy in self.marker_origins_mm[index + 1 :]:
                if math.isclose(fy, sy, abs_tol=1e-9):
                    pairs.append(("x", first, second, abs(sx - fx)))
                elif math.isclose(fx, sx, abs_tol=1e-9):
                    pairs.append(("y", first, second, abs(sy - fy)))
        return tuple(pairs)


def load_calibration_mat_profile(svg_path: Path) -> CalibrationMatProfile:
    """Parse the repository mat SVG and fail closed if its metadata disagrees with geometry."""

    raw = svg_path.read_bytes()
    try:
        root = ET.fromstring(raw)
        side = float(root.attrib["data-marker-side-mm"])
        found: list[tuple[int, float, float]] = []
        for group in root.iter(f"{_SVG}g"):
            if "data-marker-id" not in group.attrib:
                continue
            rect = group.find(f"{_SVG}rect")
            # Never drop a marker silently: transforms or size mismatches reject the mat.
            if (
                rect is None
                or "transform" in group.attrib
                or "transform" in rect.attrib
                or float(group.attrib["data-side-length-mm"]) != side
                or float(rect.attrib["width"]) != side
                or float(rect.attrib["height"]) != side
            ):
                raise PrintScaleSensitivityError("mat_svg_marker_geometry_mismatch")
            found.append(
                (
                    int(group.attrib["data-marker-id"]),
                    float(rect.attrib["x"]),
                    float(rect.attrib["y"]),
                )
            )
        markers = tuple(sorted(found))
        profile = CalibrationMatProfile(
            svg_path.stem,
            root.attrib["data-source-version"],
            hashlib.sha256(raw).hexdigest(),
            float(root.attrib["data-page-width-mm"]),
            float(root.attrib["data-page-height-mm"]),
            side,
            float(root.attrib["data-reference-distance-x-mm"]),
            float(root.attrib["data-reference-distance-y-mm"]),
            markers,
        )
    except PrintScaleSensitivityError:
        raise
    except (ET.ParseError, KeyError, ValueError) as error:
        raise PrintScaleSensitivityError("mat_svg_metadata_invalid") from error
    if len(markers) < 4:
        raise PrintScaleSensitivityError("mat_svg_requires_four_markers")
    xs = [x for _id, x, _y in markers]
    ys = [y for _id, _x, y in markers]
    if not (
        math.isclose(max(xs) - min(xs), profile.reference_distance_x_mm, abs_tol=1e-9)
        and math.isclose(max(ys) - min(ys), profile.reference_distance_y_mm, abs_tol=1e-9)
    ):
        raise PrintScaleSensitivityError("mat_svg_reference_distance_mismatch")
    return profile


@dataclass(frozen=True, slots=True)
class PrintScaleScenario:
    """Known physical/nominal ratio along the printed page x and y axes."""

    scenario_id: str
    scale_x: float
    scale_y: float
    description: str

    def __post_init__(self) -> None:
        for value in (self.scale_x, self.scale_y):
            if not _positive_finite(value):
                raise PrintScaleSensitivityError("print_scale_invalid")
            if not 0.5 <= value <= 1.5:
                raise PrintScaleSensitivityError("print_scale_out_of_simulated_range")


def fit_to_page_scale(
    profile: CalibrationMatProfile, media_width_mm: float, media_height_mm: float, margin_mm: float
) -> float:
    """Uniform scale a driver applies when 'fit to page' maps the page into the printable area."""

    return min(
        (media_width_mm - 2.0 * margin_mm) / profile.page_width_mm,
        (media_height_mm - 2.0 * margin_mm) / profile.page_height_mm,
    )


def default_print_scale_scenarios(profile: CalibrationMatProfile) -> tuple[PrintScaleScenario, ...]:
    scenarios = [PrintScaleScenario("nominal_100pct", 1.0, 1.0, "exact 100 percent print")]
    for percent in (0.5, 1.0, 2.0):
        for sign, label in ((1.0, "plus"), (-1.0, "minus")):
            delta = sign * percent / 100.0
            scenarios.append(
                PrintScaleScenario(
                    f"anisotropic_x_{label}_{percent}pct",
                    1.0 + delta,
                    1.0,
                    "printer feed/driver error along page x only",
                )
            )
            scenarios.append(
                PrintScaleScenario(
                    f"anisotropic_y_{label}_{percent}pct",
                    1.0,
                    1.0 + delta,
                    "printer feed/driver error along page y only",
                )
            )
    scenarios.append(
        PrintScaleScenario(
            "paper_shrink_humidity",
            0.999,
            0.997,
            "illustrative paper shrink: 0.1 percent machine, 0.3 percent cross direction; "
            "not a measured paper property",
        )
    )
    same_media = fit_to_page_scale(profile, profile.page_width_mm, profile.page_height_mm, 5.0)
    us_letter = fit_to_page_scale(profile, 215.9, 279.4, 5.0)
    scenarios.append(
        PrintScaleScenario(
            "fit_to_page_same_media_5mm_margin",
            same_media,
            same_media,
            "'fit to page' left enabled on the intended media with 5 mm unprintable margin",
        )
    )
    scenarios.append(
        PrintScaleScenario(
            "fit_to_page_us_letter_5mm_margin",
            us_letter,
            us_letter,
            "'fit to page' onto US Letter media with 5 mm unprintable margin",
        )
    )
    return tuple(scenarios)


@dataclass(frozen=True, slots=True)
class SimulationSettings:
    """Synthetic camera/reconstruction model; values are plausible, not device-calibrated."""

    seed: int = 20260223
    true_mm_per_reconstruction_unit: float = 0.4
    reconstruction_corner_noise_units: float = 0.05
    views_per_marker: int = 3
    pixels_per_mm_view0: float = 8.0
    corner_noise_px: float = 0.3
    image_width_px: int = 4032
    image_height_px: int = 3024
    reference_uncertainty_mm: float = 0.1
    known_object_dimensions_mm: Mapping[str, float] = field(
        default_factory=lambda: {"synthetic_bottle_height": 120.0, "synthetic_body_width": 80.0}
    )

    def __post_init__(self) -> None:
        positives = (
            self.true_mm_per_reconstruction_unit,
            self.pixels_per_mm_view0,
            self.reference_uncertainty_mm,
            *self.known_object_dimensions_mm.values(),
        )
        if any(not math.isfinite(value) or value <= 0 for value in positives):
            raise PrintScaleSensitivityError("simulation_positive_value_invalid")
        if self.reconstruction_corner_noise_units < 0 or self.corner_noise_px < 0:
            raise PrintScaleSensitivityError("simulation_noise_invalid")
        if self.views_per_marker < 1:
            raise PrintScaleSensitivityError("simulation_views_invalid")


@dataclass(frozen=True, slots=True)
class PrintedMatRulerMeasurement:
    """Owner ruler/caliper readings of the physical printed mat (never filled by software)."""

    record_reference: str
    instrument_reference: str
    measured_at_utc: str
    spacing_x_mm: float
    spacing_y_mm: float
    marker_side_mm: float

    def __post_init__(self) -> None:
        for name in ("record_reference", "instrument_reference", "measured_at_utc"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise PrintScaleSensitivityError(f"ruler_{name}_required")
        for name in ("spacing_x_mm", "spacing_y_mm", "marker_side_mm"):
            if not _positive_finite(getattr(self, name)):
                raise PrintScaleSensitivityError(f"ruler_{name}_invalid")


def check_printed_mat_spacing(
    profile: CalibrationMatProfile,
    *,
    spacing_x_mm: float | None,
    spacing_y_mm: float | None,
    marker_side_mm: float | None,
    spacing_tolerance_mm: float = DEFAULT_SPACING_TOLERANCE_MM,
    marker_side_tolerance_mm: float = DEFAULT_MARKER_SIDE_TOLERANCE_MM,
) -> dict[str, object]:
    """'Re-measure your printed mat with a ruler' gate; missing readings never pass."""

    for name, value in (
        ("spacing_tolerance_mm", spacing_tolerance_mm),
        ("marker_side_tolerance_mm", marker_side_tolerance_mm),
    ):
        if not _positive_finite(value):
            raise PrintScaleSensitivityError(f"{name}_invalid")
    for name, reading in (
        ("spacing_x_mm", spacing_x_mm),
        ("spacing_y_mm", spacing_y_mm),
        ("marker_side_mm", marker_side_mm),
    ):
        if reading is not None and not _positive_finite(reading):
            raise PrintScaleSensitivityError(f"ruler_{name}_invalid")
    readings = {
        "spacing_x": (spacing_x_mm, profile.reference_distance_x_mm, spacing_tolerance_mm),
        "spacing_y": (spacing_y_mm, profile.reference_distance_y_mm, spacing_tolerance_mm),
        "marker_side": (marker_side_mm, profile.marker_side_mm, marker_side_tolerance_mm),
    }
    if any(value is None for value, _nominal, _tol in readings.values()):
        return {"status": "OWNER_RULER_MEASUREMENT_REQUIRED", "deviations_mm": None}
    deviations = {
        name: float(value) - nominal  # type: ignore[arg-type]
        for name, (value, nominal, _tol) in readings.items()
    }
    failed = sorted(
        name for name, (_value, _nominal, tol) in readings.items() if abs(deviations[name]) > tol
    )
    return {
        "status": "REJECTED_SCALING" if failed else "WITHIN_PROVISIONAL_PRINT_TOLERANCE",
        "deviations_mm": deviations,
        "failed_readings": failed,
        "tolerances_mm": {name: tol for name, (_v, _n, tol) in readings.items()},
    }


def run_print_scale_sensitivity(
    profile: CalibrationMatProfile,
    *,
    scenarios: Sequence[PrintScaleScenario] | None = None,
    settings: SimulationSettings | None = None,
    spacing_tolerance_mm: float = DEFAULT_SPACING_TOLERANCE_MM,
    owner_ruler_measurement: PrintedMatRulerMeasurement | None = None,
) -> dict[str, object]:
    """Return a digest-bound, simulation-only sensitivity report."""

    if not _positive_finite(spacing_tolerance_mm):
        raise PrintScaleSensitivityError("spacing_tolerance_invalid")
    config = settings or SimulationSettings()
    chosen = tuple(scenarios) if scenarios is not None else default_print_scale_scenarios(profile)
    if not chosen or len({item.scenario_id for item in chosen}) != len(chosen):
        raise PrintScaleSensitivityError("scenario_ids_must_be_unique_and_non_empty")
    rng = random.Random(config.seed)
    results = [
        _simulate(profile, scenario, config, rng, spacing_tolerance_mm) for scenario in chosen
    ]
    owner_check = (
        check_printed_mat_spacing(
            profile,
            spacing_x_mm=owner_ruler_measurement.spacing_x_mm,
            spacing_y_mm=owner_ruler_measurement.spacing_y_mm,
            marker_side_mm=owner_ruler_measurement.marker_side_mm,
            spacing_tolerance_mm=spacing_tolerance_mm,
        )
        | {
            "record_reference": owner_ruler_measurement.record_reference,
            "instrument_reference": owner_ruler_measurement.instrument_reference,
            "measured_at_utc": owner_ruler_measurement.measured_at_utc,
        }
        if owner_ruler_measurement is not None
        else check_printed_mat_spacing(
            profile, spacing_x_mm=None, spacing_y_mm=None, marker_side_mm=None
        )
    )
    body: dict[str, object] = {
        "contract": REPORT_CONTRACT,
        "version": REPORT_VERSION,
        "simulation_only": True,
        "physical_validation_status": PHYSICAL_EVIDENCE_PENDING,
        "physical_claim_allowed": False,
        "physical_claim_blockers": [
            "simulation_only_synthetic_ground_truth",
            "pl0220_physical_benchmark_deferred",
            *(
                ["owner_ruler_measurement_of_printed_mat_required"]
                if owner_check["status"] != "WITHIN_PROVISIONAL_PRINT_TOLERANCE"
                else []
            ),
        ],
        "mat_profile": {
            "mat_id": profile.mat_id,
            "source_version": profile.source_version,
            "source_sha256": profile.source_sha256,
            "marker_side_mm": profile.marker_side_mm,
            "reference_distance_x_mm": profile.reference_distance_x_mm,
            "reference_distance_y_mm": profile.reference_distance_y_mm,
            "geometry_class": "nominal_svg_source_not_physical",
        },
        "simulation": {
            "seed": config.seed,
            "true_mm_per_reconstruction_unit": config.true_mm_per_reconstruction_unit,
            "reconstruction_corner_noise_units": config.reconstruction_corner_noise_units,
            "views_per_marker": config.views_per_marker,
            "pixels_per_mm_view0": config.pixels_per_mm_view0,
            "corner_noise_px": config.corner_noise_px,
            "known_object_dimensions_mm": dict(config.known_object_dimensions_mm),
            "ground_truth_class": "synthetic_software_math_check_only",
        },
        "spacing_tolerance_mm": spacing_tolerance_mm,
        "tolerance_status": "PROVISIONAL_PENDING_PL-0221",
        # A uniform print error below these ratios passes the ruler spacing gate unnoticed.
        "ruler_gate_max_undetected_relative_scale_error": {
            "x": spacing_tolerance_mm / profile.reference_distance_x_mm,
            "y": spacing_tolerance_mm / profile.reference_distance_y_mm,
        },
        "scenarios": results,
        "owner_ruler_check": owner_check,
    }
    return body | {"report_sha256": _digest(body)}


def report_digest_valid(report: Mapping[str, object]) -> bool:
    body = {key: value for key, value in report.items() if key != "report_sha256"}
    return report.get("report_sha256") == _digest(body)


def _simulate(
    profile: CalibrationMatProfile,
    scenario: PrintScaleScenario,
    config: SimulationSettings,
    rng: random.Random,
    spacing_tolerance_mm: float,
) -> dict[str, object]:
    side = profile.marker_side_mm
    k_true = config.true_mm_per_reconstruction_unit
    image_observations: list[KnownMarkerObservation] = []
    reconstruction_observations: list[ReconstructionScaleObservation] = []
    centres_units: dict[int, list[tuple[float, float]]] = {}
    for marker_id, origin_x, origin_y in profile.marker_origins_mm:
        # Physical printed corners (mm), clockwise from top-left in page coordinates.
        physical = tuple(
            (scenario.scale_x * (origin_x + dx), scenario.scale_y * (origin_y + dy))
            for dx, dy in ((0.0, 0.0), (side, 0.0), (side, side), (0.0, side))
        )
        reference = PhysicalMarkerReference(
            marker_id,
            f"{profile.mat_id}-nominal-marker-{marker_id}",
            hashlib.sha256(f"{profile.source_sha256}:{marker_id}".encode()).hexdigest(),
            side,  # the software only knows the nominal side length
            "mm",
            config.reference_uncertainty_mm,
            "synthetic_test_fixture",
        )
        for view in range(config.views_per_marker):
            ppm = config.pixels_per_mm_view0 * (1.0 + 0.05 * view)
            corners_px = tuple(
                (
                    x * ppm + rng.gauss(0.0, config.corner_noise_px),
                    y * ppm + rng.gauss(0.0, config.corner_noise_px),
                )
                for x, y in physical
            )
            if view == 0:
                image_observations.append(
                    KnownMarkerObservation(
                        marker_id,
                        corners_px,  # type: ignore[arg-type]
                        side,
                        config.reference_uncertainty_mm,
                        1.0,
                        provenance="synthetic_print_scale_proxy",
                    )
                )
            corners_units = tuple(
                (
                    x / k_true + rng.gauss(0.0, config.reconstruction_corner_noise_units),
                    y / k_true + rng.gauss(0.0, config.reconstruction_corner_noise_units),
                    0.0,
                )
                for x, y in physical
            )
            source_id = f"synthetic/{scenario.scenario_id}/view-{view}.png"
            association = AssociatedMarkerObservation(
                marker_id,
                corners_px,
                {"quality_label": "synthetic_geometry", "quality_score": 1.0},
                {"generator": REPORT_VERSION},
                source_id,
                hashlib.sha256(source_id.encode()).hexdigest(),
                config.image_width_px,
                config.image_height_px,
                f"synthetic-camera-{view}",
                _CAMERA_REVISION,
            )
            reconstruction_observations.append(
                ReconstructionScaleObservation(
                    reference,
                    ReconstructedMarkerGeometry(
                        association,
                        _RECONSTRUCTION_REVISION,
                        "reconstruction_units",
                        corners_units,  # type: ignore[arg-type]
                        max(config.reconstruction_corner_noise_units, 1e-6),
                    ),
                )
            )
            centres_units.setdefault(marker_id, []).append(
                (
                    sum(point[0] for point in corners_units) / 4.0,
                    sum(point[1] for point in corners_units) / 4.0,
                )
            )

    image_estimate = estimate_scale(image_observations)
    estimate = estimate_reconstruction_scale(
        tuple(reconstruction_observations),
        reconstruction_revision=_RECONSTRUCTION_REVISION,
        camera_solution_revision=_CAMERA_REVISION,
    )
    # The software trusts the nominal side, so it under-reads mm/unit by 2 / (sx + sy).
    analytic_relative_error = 2.0 / (scenario.scale_x + scenario.scale_y) - 1.0
    result: dict[str, object] = {
        "scenario_id": scenario.scenario_id,
        "description": scenario.description,
        "print_scale_x": scenario.scale_x,
        "print_scale_y": scenario.scale_y,
        "analytic_relative_scale_error": analytic_relative_error,
        "reconstruction_estimator_status": estimate.status,
        "reconstruction_estimator_errors": list(estimate.errors),
        "image_estimator_status": image_estimate.status,
    }
    if image_estimate.mm_per_pixel is not None:
        result["image_estimator_relative_scale_error"] = (
            image_estimate.mm_per_pixel * config.pixels_per_mm_view0 - 1.0
        )
    if estimate.reconstruction_units_to_mm is None:
        result["metric_scale_usable"] = False
        return result
    factor = estimate.reconstruction_units_to_mm
    relative_error = factor / k_true - 1.0
    relative_uncertainty = (estimate.uncertainty_mm_per_reconstruction_unit or 0.0) / factor
    centres = {
        marker_id: (
            sum(point[0] for point in values) / len(values),
            sum(point[1] for point in values) / len(values),
        )
        for marker_id, values in centres_units.items()
    }
    spacings = []
    for axis, first, second, nominal in profile.spacing_pairs():
        image_derived = math.dist(centres[first], centres[second]) * factor
        simulated_ruler = nominal * (scenario.scale_x if axis == "x" else scenario.scale_y)
        spacings.append(
            {
                "axis": axis,
                "marker_ids": [first, second],
                "nominal_mm": nominal,
                "image_derived_mm": image_derived,
                "image_derived_deviation_mm": image_derived - nominal,
                "image_derived_flagged": abs(image_derived - nominal) > spacing_tolerance_mm,
                "simulated_ruler_reading_mm": simulated_ruler,
                "simulated_ruler_flagged": abs(simulated_ruler - nominal) > spacing_tolerance_mm,
            }
        )
    result |= {
        "metric_scale_usable": True,
        "metric_state": estimate.metric_state,
        "estimated_mm_per_reconstruction_unit": factor,
        "true_mm_per_reconstruction_unit": k_true,
        "relative_scale_error": relative_error,
        "estimator_relative_uncertainty": relative_uncertainty,
        "bias_within_estimator_2sigma": abs(relative_error) <= 2.0 * relative_uncertainty,
        "object_dimension_propagation": [
            {
                "dimension_id": name,
                "true_mm": true_mm,
                "measured_mm": (true_mm / k_true) * factor,
                "error_mm": (true_mm / k_true) * factor - true_mm,
            }
            for name, true_mm in sorted(config.known_object_dimensions_mm.items())
        ],
        "spacing_checks": spacings,
        "detected_by_image_spacing": any(item["image_derived_flagged"] for item in spacings),
        "detected_by_simulated_ruler": any(item["simulated_ruler_flagged"] for item in spacings),
    }
    return result


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()
