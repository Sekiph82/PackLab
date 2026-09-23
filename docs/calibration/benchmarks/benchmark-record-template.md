# PackLab first physical benchmark record template

Copy this file to an owner-controlled record for one physical benchmark
session. Replace placeholders only with owner-controlled evidence. This public
template intentionally contains no physical measurements, iPhone execution
result, printer result, or benchmark statistic.

## Record identity and provenance

- `record_version`: `1.0.0`
- `record_id`: `[OWNER ASSIGNED STABLE ID]`
- `status`: `OWNER_REQUIRED`
- `provenance`: `owner_physical_session`
- `created_at_utc`: `[ENTER RFC3339 UTC TIMESTAMP OR UNRECORDED]`
- `operator_reference`: `[SAFE OWNER REFERENCE OR UNRECORDED]`
- `raw_evidence_reference`: `[PRIVATE STORE ID/HASH OR UNRECORDED]`
- `public_evidence_reference`: `[SAFE PUBLIC ID/URL OR UNRECORDED]`

## Mat and accepted printed verification

- `mat_asset`: `[assets/calibration/a4-packlab-calibration-mat.svg OR A3 PATH]`
- `mat_source_revision_or_sha256`: `[ENTER SOURCE ID]`
- `mat_attempt_reference`: `[OWNER PRINT ATTEMPT ID OR UNRECORDED]`
- `verification_record_reference`: `[LINK/ID OF OWNER VERIFICATION RECORD]`
- `verification_record_status`: `UNRECORDED`
- `verification_record_private_reference`: `[PRIVATE RECORD ID OR UNRECORDED]`
- `known_dimension_field`: `marker_side_id_0`
- `known_dimension_unit`: `mm`
- `known_dimension_mm`: `UNRECORDED`
- `known_dimension_provenance`: `owner_measured_geometry_from_accepted_verification_record`

The benchmark cannot become `READY_FOR_AUDIT` or `COMPLETE` unless the linked
verification record is `ACCEPTED_FOR_CAPTURE` and the known dimension is an
owner-measured value. Nominal SVG geometry is not a physical measurement.

## Device, lens and capture binding

- `device_model`: `iPhone 16 Standard`
- `lens_identity`: `main_wide_camera_1x`
- `camera_position`: `back`
- `image_width_px`: `UNRECORDED`
- `image_height_px`: `UNRECORDED`
- `orientation`: `UNRECORDED`
- `coordinate_convention`: `image_pixels_origin_top_left_detector_order`
- `zoom_factor`: `UNRECORDED`
- `focus_mode`: `UNRECORDED`
- `focus_distance_m`: `UNRECORDED`
- `capture_app_version`: `UNRECORDED`
- `calibration_model_version`: `UNRECORDED`
- `calibration_policy_version`: `UNRECORDED`

## Capture conditions and sample accounting

- `capture_timestamp_start_utc`: `UNRECORDED`
- `capture_timestamp_end_utc`: `UNRECORDED`
- `lighting_conditions`: `UNRECORDED`
- `background_surface`: `UNRECORDED`
- `camera_to_mat_setup`: `UNRECORDED`
- `required_view_count`: `7`
- `candidate_sample_count`: `UNRECORDED`
- `accepted_sample_count`: `UNRECORDED`
- `rejected_sample_count`: `UNRECORDED`
- `invalid_or_unavailable_sample_count`: `UNRECORDED`
- `missing_measurement_count`: `UNRECORDED`

Every candidate sample, including rejected and invalid samples, must appear in
the table below. Do not delete a row because its estimate is unavailable.

## Per-sample results

| Sample ID | Required view | Status (`ACCEPTED`/`REJECTED`/`INVALID`) | Evidence reference | Reject/invalid reason | Known dimension (mm) | Estimated dimension (mm) | Signed error (mm) | Absolute error (mm) | Percentage error (%) |
| --- | --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| `[SAMPLE-001]` | `[PL-0065 view]` | `UNRECORDED` | `[PRIVATE ID/HASH]` | `[NONE OR REASON]` | `UNRECORDED` | `UNRECORDED` | `UNRECORDED` | `UNRECORDED` | `UNRECORDED` |
| `[SAMPLE-002]` | `[PL-0065 view]` | `UNRECORDED` | `[PRIVATE ID/HASH]` | `[NONE OR REASON]` | `UNRECORDED` | `UNRECORDED` | `UNRECORDED` | `UNRECORDED` | `UNRECORDED` |

Add rows; do not replace rejected samples with successful retries. A retry gets
a new sample ID and the original row remains retained.

## Formulas and units

All dimensional values in this section are in millimetres unless explicitly
labelled otherwise.

- `signed_error_mm = estimated_dimension_mm - known_dimension_mm`
- `absolute_error_mm = abs(signed_error_mm)`
- `percentage_error = (absolute_error_mm / known_dimension_mm) * 100`
- `signed_percentage_error = (signed_error_mm / known_dimension_mm) * 100`

Only a sample with status `ACCEPTED`, finite positive known dimension and a
finite estimated dimension may receive numeric error fields. Otherwise use
`UNRECORDED` and retain the rejection/invalid reason.

## Aggregate statistics

- `total_rows_recorded`: `UNRECORDED`
- `accepted_rows_in_error_aggregate`: `UNRECORDED`
- `rejected_rows_retained`: `UNRECORDED`
- `invalid_rows_retained`: `UNRECORDED`
- `rows_missing_measurement`: `UNRECORDED`
- `mean_signed_error_mm_accepted`: `UNRECORDED`
- `mean_absolute_error_mm_accepted`: `UNRECORDED`
- `mean_percentage_error_accepted`: `UNRECORDED`
- `max_absolute_error_mm_accepted`: `UNRECORDED`
- `aggregate_formula_reference`: `arithmetic_mean_over_numeric_ACCEPTED_rows_only; counts include every recorded row`
- `threshold_status`: `NOT_SET_FROM_THIS_SESSION`
- `provisional_gate_reference`: `docs/calibration/confidence-thresholds.md`

The aggregate denominator and every excluded row category must be explicit.
Rejected or invalid rows are not silently treated as zero and are not silently
removed from the record. No physical acceptance threshold is inferred from an
empty or single benchmark session.

## Owner decision and evidence references

- `owner_physical_measurement_complete`: `UNRECORDED`
- `owner_native_capture_complete`: `UNRECORDED`
- `owner_acceptance_decision`: `OWNER_REQUIRED`
- `owner_signature_or_controlled_reference`: `[ENTER OR UNRECORDED]`
- `notes_and_limitations`: `[ENTER OBSERVATIONS; DO NOT BACKFILL MISSING DATA]`

Final public status remains `OWNER_REQUIRED` until the owner supplies and
authorizes references to the accepted printed-mat verification and physical
capture/measurement evidence.
