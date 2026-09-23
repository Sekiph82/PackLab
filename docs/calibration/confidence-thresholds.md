# PackLab calibration confidence thresholds

`score_calibration_confidence` assigns a deterministic, dimensionless
confidence score from an already computed `ScaleEstimate`. It is a consistency
gate for PackLab calibration records; it is not a physical accuracy claim and
was not tuned from printed-mat or device benchmark data.

## Score factors

The score is clamped to the closed interval `[0, 1]` and rounded to six decimal
places. Its unit is `dimensionless_0_to_1`.

`score = 0.35 * count_factor + 0.40 * residual_factor + 0.25 * spread_factor`

- `count_factor`: accepted marker count divided by 4, capped at 1.0. Four or
  more markers receive full count credit; two accepted markers are still the
  mathematical minimum inherited from scale estimation.
- `residual_factor`: `1 - max_relative_residual / 0.05`, clamped to `[0, 1]`.
  `max_relative_residual` is a unitless fraction of the estimated
  `mm_per_pixel` scale. `0.05` is a hard maximum consistency gate: exact
  `0.05` is allowed, but any value greater than `0.05` rejects fail-closed
  before score-state assignment.
- `spread_factor`: `1 - max_relative_edge_spread / 0.03`, clamped to `[0, 1]`.
  `max_relative_edge_spread` is a unitless fraction computed from each marker's
  four edge lengths in image pixels. `0.03` is a hard maximum consistency gate:
  exact `0.03` is allowed, but any value greater than `0.03` rejects
  fail-closed before score-state assignment.

The residual and edge-spread thresholds are provisional synthetic consistency
gates. They must remain labelled provisional until owner-controlled physical
benchmark evidence exists.

## Frozen states

- `accepted`: score is greater than or equal to `0.80`.
- `warning`: score is greater than or equal to `0.60` and below `0.80`.
- `rejected`: score is below `0.60`; the input scale estimate is already
  rejected/missing its usable scale; `max_relative_residual` is greater than
  `0.05`; or `max_relative_edge_spread` is greater than `0.03`.

Only `accepted` and `warning` return `usable_for_capture = true`. `rejected`
fails closed with `usable_for_capture = false`.

This stage uses synthetic and contract-level evidence only. It does not use
printer measurements, iPhone camera intrinsics, device APIs, native capture, or
physical benchmark evidence.
