# PackLab millimetre scale estimation

`estimate_scale` uses the explicit convention

`sample_mm_per_pixel = known_marker_side_mm / mean(four ordered image-edge lengths in pixels)`

and combines accepted samples with inverse-variance weights. A sample's
uncertainty includes its known-geometry uncertainty and edge-length spread,
then is adjusted by its quality score. The result reports `mm_per_pixel`, the
inverse `pixels_per_mm`, propagated uncertainty, per-marker residuals, samples
used/rejected, and a versioned provenance record. Millimetres are the only
real-world unit; corners are image pixels in the detector's ordered
top-left/clockwise convention.

At least two accepted valid observations are required. Partial/unaccepted
observations, non-positive or degenerate geometry, non-finite values, and
quality outside `(0, 1]` are not used. If accepted samples disagree by more
than the provisional 5% relative residual threshold, the estimate is
`rejected` with no usable scale value. These thresholds are mathematical
consistency gates, not a claim of physical measurement accuracy.

This stage does not use printer measurements, camera intrinsics, device APIs,
or physical benchmark data. Synthetic tests cover exact, noisy, inconsistent,
insufficient, and rejected-observation cases.
