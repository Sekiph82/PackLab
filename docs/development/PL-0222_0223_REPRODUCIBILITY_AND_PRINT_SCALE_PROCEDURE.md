# PL-0222 / PL-0223 repeat-scan reproducibility and mat print-scale procedure

Status: software proxy implemented. Physical evidence is still **PHYSICAL_EVIDENCE_PENDING**.
Both tasks remain blocked on the owner-deferred PL-0220 physical benchmark. Synthetic results
only show that the software math is correct. They are not a physical PASS, and they do not
show physical accuracy or repeatability.

Code:

- `core/src/packlab_core/print_scale_sensitivity.py` (PL-0223)
- `core/src/packlab_core/repeat_scan_reproducibility.py` (PL-0222)
- Tests: `tests/core/test_print_scale_sensitivity.py` and
  `tests/core/test_repeat_scan_reproducibility.py`

## What the software proxy establishes

**PL-0223.** Suppose a mat prints at physical/nominal ratios `sx`, `sy`. The real
`estimate_scale` and `estimate_reconstruction_scale` both assume the nominal 40 mm marker
side. So both return mm/unit factors that are wrong by `2/(sx+sy) - 1`, and every object
dimension carries that same relative error. Noise-free tests check this to 1e-12, and the
seeded-noise tests check it to within 3 sigma of the estimator. Uniform errors such as
"fit to page" (a 5.0 % error for A4 with 5 mm margins) are accepted by both estimators. The
estimators' own uncertainty does not cover that bias, and image-derived marker spacing cannot
see it either. **Only a ruler measurement of the printed mat catches a uniform print-scale
error.** The default ±1.0 mm spacing gate lets a uniform error of up to 1/150 (0.67 %) on
x and 1/207 (0.48 %) on y on an A4 mat go undetected. The report records these limits as
`ruler_gate_max_undetected_relative_scale_error`.

Two inputs fail closed:

- `check_printed_mat_spacing` rejects any reading or tolerance that is NaN, infinite, zero,
  negative or bool. Only a missing reading returns `OWNER_RULER_MEASUREMENT_REQUIRED`.
- The SVG loader rejects the whole mat, rather than dropping a marker, when a marker group or
  rect has a transform or a size that differs from the mat's side length, when fewer than
  four markers exist, or when the marker positions disagree with the reference distances.

**PL-0222.** N scans are each registered to a reference scan with the accepted rigid
`register_repeat_scans` path, which never scales. The proxy then reports:

- Per-axis overall extents in the reference frame: mean, sample std, min/max, max |dev|, RMS
  dev and `RC95 = 1.96*sqrt(2)*std`.
- Pooled scan-to-reference residual distances: mean, std, max, RMS and a nearest-rank
  `p95_distance`. Distances are unsigned, so this is a percentile, not a Bland-Altman
  coefficient. Only ICP inliers are pooled, and those are capped at
  `maximum_correspondence_distance`. The p95 therefore can never exceed that gate. The report
  records the gate as `surface_residuals_truncated_at_correspondence_distance`, and the run
  fails closed unless the gate is strictly larger than `maximum_surface_deviation_p95`.

It flags three kinds of scan:

- `partial_coverage`: the reverse-registration fitness is below the minimum coverage.
- `scale_outlier`: the mean relative extent deviates from the median of fully covered scans
  by more than the tolerance.
- `registration_not_accepted`.

Flagged scans are excluded from the dimension statistics. Scale outliers and failed
registrations are also excluded from the surface statistics. Inputs fail closed when scale
states are mixed, when an input is RELATIVE, or when a scale provenance is missing,
mismatched or factorless. They also fail closed when two scans share one scale provenance,
when revision IDs repeat, or when a consensus extent is zero.

`simulation_only` is always true in this version. `RegistrationRevision` forbids
METRIC_VERIFIED, so no owner-signed record can be bound to the scans here. The separate field
`scale_evidence_class_claimed_physical` is true when every used marker reference is
*labelled* `accepted_owner_physical`. That label is a caller assertion
(`scale_evidence_class_basis: caller_asserted_label_not_owner_record_bound`). It is necessary
but not sufficient, and on its own it does NOT close PL-0222. It must be checked against the
retained owner verification record. Use `report_digest_valid` to check a stored report.

All thresholds are labelled `PROVISIONAL_PENDING_PL-0221`.

## Operator procedure (owner, once a printer and benchmark objects exist)

### PL-0223 printed-mat print-scale check

1. Print the A4 or A3 v1.0.1 SVG at 100 % / actual size, with fit-to-page and scale-to-media
   off. Follow `docs/calibration/pre-use-verification.md`.
2. Use a ruler or caliper to measure the x and y marker-centre distances and one marker side.
   Take two readings each and record them in the verification record template.
3. Build a `PrintedMatRulerMeasurement` from those readings. Use safe references only: no
   serial numbers, supplier data or private paths. Then run
   `run_print_scale_sensitivity(load_calibration_mat_profile(svg), owner_ruler_measurement=...)`.
4. `owner_ruler_check.status` must be `WITHIN_PROVISIONAL_PRINT_TOLERANCE`. If it is
   `REJECTED_SCALING`, keep the record, fix the print settings and reprint. If it is
   `OWNER_RULER_MEASUREMENT_REQUIRED`, no physical claim is possible.
5. Convert the measured spacing to a relative error (`measured/nominal - 1`). Compare it with
   the report's `ruler_gate_max_undetected_relative_scale_error` and decide whether the
   provisional gate is tight enough for the PL-0221 thresholds.

**Evidence that closes PL-0223:**

- A retained owner verification record for a real printed mat, with readings, instrument
  reference and timestamp.
- The digest-bound sensitivity report run with those readings.
- At least one real capture of that mat with the PL-0220 benchmark objects. Its metric scale
  error must be compared against caliper ground truth and must be consistent with the
  simulated sensitivity.
- An independent reviewer audit.

Simulation alone never closes it.

### PL-0222 repeat-scan reproducibility

1. Scan the same benchmark object (matte bottle, glossy bottle, jerrycan) at least 3 times,
   ideally 5 or more. Re-place the object and the mat between scans. Use the same device,
   capture profile and mat record each time.
2. Each scan needs its own scale provenance, built from that capture's marker observations.
   Distinct provenance IDs are enforced. The code does not check that each provenance's
   `input_reconstruction_revision` belongs to that scan, so the reviewer must check it.
   Build `RegistrationRevision`s from Scan Master or Object Capture Geometry revisions in
   METRIC_UNVERIFIED state.
3. Run `evaluate_repeat_scan_reproducibility(revisions, {id: provenance}, policy=...)`. Set
   the correspondence gate above the expected residual. Supply `initial_transforms` when
   scans are not already roughly aligned.
4. Review the flagged scans. Do not delete a scale outlier to improve the statistics: keep
   it and investigate its mat and scale provenance. Partial-coverage scans must be recaptured
   before their dimensions count.
5. Compare the extent RC95 and the surface p95 with the PL-0221 thresholds once those are
   accepted. Compare the per-scan dimensions with caliper ground truth from the PL-0220
   benchmark record.

**Evidence that closes PL-0222:**

- At least 3 real repeat scans per benchmark category. Each scan's scale provenance must
  trace to a retained owner verification record. A
  `scale_evidence_class_claimed_physical: true` flag is a caller claim, not proof. A later
  revision must add an owner-record binding before `simulation_only` can ever be false.
- The digest-bound reproducibility report.
- Caliper ground truth from PL-0220.
- Thresholds from an accepted PL-0221.
- An independent reviewer audit.

Until then, `physical_validation_status` stays `PHYSICAL_EVIDENCE_PENDING` and
`mold_use_authorized` stays false.

## Known limits of the proxy

- Extents are sample max-min values, so noise biases them upward by about 2-3 sigma. For
  example, with sigma = 0.05 the 100 mm extent reads about 100.22. Use them for spread, not
  absolute size.
- Surface deviation is measured scan-to-reference with nearest-neighbour correspondences,
  not across all pairs. The `sigma*sqrt(6)` recovery in the tests depends on the synthetic
  scans sharing a sample grid.
- The scale-outlier test cannot separate a true object-size change from a scale-provenance
  error. Either one needs owner investigation.
- The print model is an affine x/y page scale. It does not model local warping, cockle,
  non-planar mats, lens distortion or a tilted camera. The synthetic camera and noise values
  are plausible but not calibrated to a device.
- The paper-shrink scenario values are illustrative, not measured paper properties.
