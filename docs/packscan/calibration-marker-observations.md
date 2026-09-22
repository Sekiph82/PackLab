# PackScan calibration marker observations

`calibration/marker-observations.json` is the versioned image-space contract
for calibration markers. It records the marker family and dictionary, marker
ID, image corners in pixel coordinates, detector confidence/quality, and
known marker geometry. The schema is
`schemas/packscan/calibration-marker-observations.schema.json`.

## Units and conversion

Millimetres (`mm`) are the only canonical real-world unit stored in a marker
geometry record. A producer that measures a mat in metres, centimetres, or
inches must convert to millimetres before writing the `side_length`; the
conversion is `mm = source_value * source_unit_to_mm_factor`. Stored values
are rounded using the declared `precision.decimal_places` and
`round_half_even` rule. A unitless number is not a scale value and is rejected
by the contract. Pixel corners remain image pixels and are not converted to
millimetres.

The schema's optional `conversion` object records the conversion rule and
accepted input units. It does not permit a producer to omit the unit from the
stored geometry.

## Geometry provenance and eligibility

Every valid marker's known square side length requires a positive value, the
`mm` unit token, and a provenance source plus reference. A reference may be a
mat specification, an operator measurement, a calibration record, or a
manufacturer specification. Nominal geometry is not evidence that a printer
or physical mat has been verified.

`valid` observations have exactly four ordered image corners, known geometry,
and `scale_eligibility: eligible`. `partial` or `ambiguous` observations may
retain one through four observed corners and a reason, but they must have
`scale_eligibility: not_eligible` and cannot include known geometry. The
top-level `scale_truth_status` is `usable` only when at least one valid
observation exists; an observation marked partial or ambiguous never becomes
scale truth by itself.

The corner convention is image coordinates with `x` increasing right and `y`
increasing down. Producers must preserve the detector's documented clockwise
corner order; this schema intentionally does not infer physical scale from
pixel coordinates alone.

Fixtures in `tests/fixtures/packscan/` are tiny synthetic public examples. They
are contract-validation inputs, not camera, printer, device, or physical
accuracy evidence.
