"""Provenance-bound uncertainty propagation and presentation for measurements."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .bounding_dimensions import NormalizedMeasurementGeometry
from .reconstruction import ScaleState

UNCERTAINTY_METHOD_VERSION = "independent_standard_uncertainty_rss_scale_power_v1"
MAX_QUANTITY_POWER = 3


class MeasurementUncertaintyError(ValueError):
    """Raised when uncertainty evidence is invalid, stale, or unit-incompatible."""


@dataclass(frozen=True, slots=True)
class NormalizationScaleEvidence:
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    scale_factor_mm_per_reconstruction_unit: float
    factor_standard_uncertainty: float | None
    factor_uncertainty_unit: str

    def __post_init__(self) -> None:
        for name in ("source_geometry_id", "normalized_geometry_revision"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise MeasurementUncertaintyError(f"normalization_{name}_required")
        if not isinstance(self.scale_state, ScaleState) or self.scale_state is ScaleState.RELATIVE:
            raise MeasurementUncertaintyError("normalization_scale_state_invalid")
        if not isinstance(self.scale_provenance_id, str) or not self.scale_provenance_id.strip():
            raise MeasurementUncertaintyError("normalization_scale_provenance_required")
        if not _positive_finite(self.scale_factor_mm_per_reconstruction_unit):
            raise MeasurementUncertaintyError("normalization_scale_factor_invalid")
        if self.factor_standard_uncertainty is not None and not _nonnegative_finite(
            self.factor_standard_uncertainty
        ):
            raise MeasurementUncertaintyError("normalization_scale_uncertainty_invalid")
        if self.factor_uncertainty_unit != "mm_per_reconstruction_unit":
            raise MeasurementUncertaintyError("normalization_scale_uncertainty_unit_invalid")


@dataclass(frozen=True, slots=True)
class MeasurementUncertaintyInput:
    measurement_id: str
    value: float
    value_unit: str
    quantity_power: int
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    measurement_standard_uncertainty: float | None = None
    measurement_uncertainty_unit: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.measurement_id, str) or not self.measurement_id.strip():
            raise MeasurementUncertaintyError("measurement_id_required")
        if not _finite(self.value) or self.value < 0.0:
            raise MeasurementUncertaintyError("measurement_value_must_be_finite_nonnegative")
        if not isinstance(self.value_unit, str) or not self.value_unit.strip():
            raise MeasurementUncertaintyError("measurement_value_unit_required")
        if (
            not isinstance(self.quantity_power, int)
            or isinstance(self.quantity_power, bool)
            or not 1 <= self.quantity_power <= MAX_QUANTITY_POWER
        ):
            raise MeasurementUncertaintyError("measurement_quantity_power_invalid")
        if self.measurement_standard_uncertainty is None:
            if self.measurement_uncertainty_unit is not None:
                raise MeasurementUncertaintyError("measurement_uncertainty_unit_without_value")
        elif not _nonnegative_finite(self.measurement_standard_uncertainty):
            raise MeasurementUncertaintyError("measurement_standard_uncertainty_invalid")
        elif self.measurement_uncertainty_unit != self.value_unit:
            raise MeasurementUncertaintyError("measurement_uncertainty_unit_incompatible")


@dataclass(frozen=True, slots=True)
class MeasurementUncertaintyReport:
    report_id: str
    measurement_id: str
    source_geometry_id: str
    normalized_geometry_revision: str
    scale_provenance_id: str | None
    scale_state: ScaleState
    estimate: float
    estimate_unit: str
    quantity_power: int
    propagated_standard_uncertainty: float | None
    uncertainty_unit: str
    uncertainty_status: str
    components: tuple[dict[str, object], ...]
    confidence_score: float | None
    confidence_interpretation: str | None
    estimate_display: str
    uncertainty_display: str

    def as_dict(self) -> dict[str, object]:
        return {
            "contract": "packlab.measurement-uncertainty.v1",
            "report_id": self.report_id,
            "method_version": UNCERTAINTY_METHOD_VERSION,
            "measurement_link": {
                "measurement_id": self.measurement_id,
                "source_geometry_id": self.source_geometry_id,
                "normalized_geometry_revision": self.normalized_geometry_revision,
                "scale_provenance_id": self.scale_provenance_id,
                "scale_state": self.scale_state.value,
            },
            "estimate": self.estimate,
            "estimate_unit": self.estimate_unit,
            "quantity_power": self.quantity_power,
            "propagated_standard_uncertainty": self.propagated_standard_uncertainty,
            "uncertainty_unit": self.uncertainty_unit,
            "uncertainty_status": self.uncertainty_status,
            "components": [dict(item) for item in self.components],
            "confidence": {
                "score": self.confidence_score,
                "interpretation": self.confidence_interpretation,
                "converted_to_physical_tolerance": False,
            },
            "presentation": {
                "estimate": self.estimate_display,
                "uncertainty": self.uncertainty_display,
                "rounding": "two significant digits for known uncertainty; estimate rounded to the same decimal place",
                "false_precision_claimed": False,
            },
            "unknown_or_unmodeled_sources": [
                "capture_and_reconstruction_geometry_uncertainty_not_supplied",
                "normalization_orientation_uncertainty_not_supplied",
                "feature_or_surface_sampling_uncertainty_not_a_standard_uncertainty",
            ],
            "physical_accuracy_claimed": False,
        }


def propagate_measurement_uncertainty(
    geometry: NormalizedMeasurementGeometry,
    measurement: MeasurementUncertaintyInput,
    *,
    normalization_scale: NormalizationScaleEvidence | None,
    confidence_score: float | None = None,
    confidence_interpretation: str | None = None,
) -> MeasurementUncertaintyReport:
    """Combine compatible standard uncertainties and keep unknown inputs explicit."""

    _validate_measurement_link(geometry, measurement)
    if confidence_score is None:
        if confidence_interpretation is not None:
            raise MeasurementUncertaintyError("confidence_interpretation_without_score")
    else:
        if not _unit_interval(confidence_score):
            raise MeasurementUncertaintyError("confidence_score_out_of_range")
        if (
            not isinstance(confidence_interpretation, str)
            or "not physical tolerance" not in confidence_interpretation.casefold()
        ):
            raise MeasurementUncertaintyError("confidence_must_be_labeled_not_physical_tolerance")

    components: list[dict[str, object]] = []
    known_variances: list[float] = []
    scale_status: str
    if geometry.scale_state is ScaleState.RELATIVE:
        if normalization_scale is not None:
            raise MeasurementUncertaintyError("relative_geometry_cannot_bind_metric_scale_evidence")
        scale_status = "not_applicable_relative_scale"
    else:
        if normalization_scale is None:
            scale_status = "unknown_normalization_scale_evidence_missing"
        else:
            _validate_scale_link(geometry, normalization_scale)
            if normalization_scale.factor_standard_uncertainty is None:
                scale_status = "unknown_scale_factor_uncertainty_missing"
            else:
                relative_factor_uncertainty = (
                    normalization_scale.factor_standard_uncertainty
                    / normalization_scale.scale_factor_mm_per_reconstruction_unit
                )
                scale_component = (
                    abs(measurement.value)
                    * measurement.quantity_power
                    * relative_factor_uncertainty
                )
                components.append(
                    {
                        "name": "normalization_scale_factor",
                        "value": scale_component,
                        "unit": measurement.value_unit,
                        "status": "propagated_first_order",
                        "method": "quantity_power * abs(estimate) * factor_standard_uncertainty / factor",
                        "input_factor_unit": normalization_scale.factor_uncertainty_unit,
                    }
                )
                known_variances.append(scale_component**2)
                scale_status = "known"

    if measurement.measurement_standard_uncertainty is not None:
        if measurement.measurement_uncertainty_unit != measurement.value_unit:
            raise MeasurementUncertaintyError("measurement_uncertainty_unit_incompatible")
        components.append(
            {
                "name": "measurement_standard_uncertainty",
                "value": measurement.measurement_standard_uncertainty,
                "unit": measurement.value_unit,
                "status": "known_input",
                "method": "independent standard uncertainty supplied by measurement evidence",
            }
        )
        known_variances.append(measurement.measurement_standard_uncertainty**2)

    combined = math.sqrt(math.fsum(known_variances)) if known_variances else None
    if combined is None:
        uncertainty_status = (
            "unknown_relative_scale_not_physical"
            if scale_status == "not_applicable_relative_scale"
            else scale_status
        )
    elif scale_status.startswith("unknown"):
        uncertainty_status = "partial_known_components_scale_unknown"
    elif geometry.scale_state is ScaleState.RELATIVE:
        uncertainty_status = "known_relative_coordinate_uncertainty_only"
    else:
        uncertainty_status = "known_propagated_components_only"

    if combined is None:
        estimate_display = _format_significant(measurement.value, 3) + f" {measurement.value_unit}"
        uncertainty_display = "unknown"
    else:
        estimate_display = _format_with_uncertainty_precision(
            measurement.value, combined, measurement.value_unit
        )
        uncertainty_display = f"± {_format_significant(combined, 2)} {measurement.value_unit}"
    body: dict[str, object] = {
        "measurement_id": measurement.measurement_id,
        "source_geometry_id": geometry.source_geometry_id,
        "normalized_geometry_revision": geometry.normalized_geometry_revision,
        "scale_provenance_id": geometry.scale_provenance_id,
        "scale_state": geometry.scale_state.value,
        "estimate": measurement.value,
        "estimate_unit": measurement.value_unit,
        "quantity_power": measurement.quantity_power,
        "propagated_standard_uncertainty": combined,
        "uncertainty_status": uncertainty_status,
        "components": components,
        "confidence_score": confidence_score,
        "confidence_interpretation": confidence_interpretation,
    }
    report_id = (
        "measurement-uncertainty:"
        + hashlib.sha256(
            json.dumps(body, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("ascii")
        ).hexdigest()
    )
    return MeasurementUncertaintyReport(
        report_id,
        measurement.measurement_id,
        geometry.source_geometry_id,
        geometry.normalized_geometry_revision,
        geometry.scale_provenance_id,
        geometry.scale_state,
        measurement.value,
        measurement.value_unit,
        measurement.quantity_power,
        combined,
        measurement.value_unit,
        uncertainty_status,
        tuple(components),
        confidence_score,
        confidence_interpretation,
        estimate_display,
        uncertainty_display,
    )


def serialize_measurement_uncertainty(report: MeasurementUncertaintyReport) -> bytes:
    return json.dumps(
        report.as_dict(), sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("ascii")


def _validate_measurement_link(
    geometry: NormalizedMeasurementGeometry,
    measurement: MeasurementUncertaintyInput,
) -> None:
    if (
        measurement.source_geometry_id != geometry.source_geometry_id
        or measurement.normalized_geometry_revision != geometry.normalized_geometry_revision
        or measurement.scale_provenance_id != geometry.scale_provenance_id
        or measurement.scale_state is not geometry.scale_state
    ):
        raise MeasurementUncertaintyError("measurement_provenance_link_mismatch")
    base_unit = {
        ScaleState.RELATIVE: "reconstruction_units",
        ScaleState.METRIC_UNVERIFIED: "mm_unverified",
        ScaleState.METRIC_VERIFIED: "mm",
    }[geometry.scale_state]
    expected_unit = _quantity_unit(base_unit, measurement.quantity_power)
    if measurement.value_unit != expected_unit:
        raise MeasurementUncertaintyError("measurement_unit_conflicts_with_scale_state")


def _validate_scale_link(
    geometry: NormalizedMeasurementGeometry,
    scale: NormalizationScaleEvidence,
) -> None:
    if (
        scale.source_geometry_id != geometry.source_geometry_id
        or scale.normalized_geometry_revision != geometry.normalized_geometry_revision
        or scale.scale_provenance_id != geometry.scale_provenance_id
        or scale.scale_state is not geometry.scale_state
    ):
        raise MeasurementUncertaintyError("normalization_scale_provenance_link_mismatch")
    if geometry.scale_factor_uncertainty != scale.factor_standard_uncertainty:
        raise MeasurementUncertaintyError("normalization_scale_uncertainty_input_mismatch")
    if geometry.scale_provenance_record is not None:
        if (
            geometry.scale_provenance_record.estimated_scale_factor_mm_per_reconstruction_unit
            != scale.scale_factor_mm_per_reconstruction_unit
        ):
            raise MeasurementUncertaintyError("normalization_scale_factor_provenance_mismatch")


def _format_significant(value: float, digits: int) -> str:
    if value == 0.0:
        return "0"
    decimal = Decimal(str(abs(value)))
    quantum = Decimal(1).scaleb(decimal.adjusted() - digits + 1)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    return format(rounded, "f")


def _format_with_uncertainty_precision(value: float, uncertainty: float, unit: str) -> str:
    decimal_uncertainty = Decimal(str(abs(uncertainty)))
    if decimal_uncertainty == 0:
        return f"{_format_significant(value, 3)} {unit}"
    quantum = Decimal(1).scaleb(decimal_uncertainty.adjusted() - 1)
    rounded_value = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    return f"{format(rounded_value, 'f')} {unit}"


def _finite(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _positive_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0.0
    )


def _nonnegative_finite(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0.0
    )


def _unit_interval(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and 0.0 <= value <= 1.0
    )


def _quantity_unit(base_unit: str, power: int) -> str:
    return base_unit if power == 1 else f"{base_unit}^{power}"
