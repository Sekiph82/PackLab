# PackScan camera intrinsics

Intrinsics use a row-major homogeneous 3x3 matrix:

```text
| fx  0  cx |
|  0 fy  cy |
|  0  0   1 |
```

Pixel coordinates originate at the centre of the top-left stored pixel, with
`x` increasing right and `y` increasing down. `reference_dimensions` identify
the image dimensions for which the matrix was measured. With
`uniform_scale_about_origin`, a target image scales `fx`, `fy`, `cx`, and `cy`
by the same `target/reference` factor; non-uniform aspect-ratio changes are
rejected. `exact_reference_only` rejects any dimension mismatch.

Lens identity, status (`measured`, `estimated`, or `unavailable`), source, UTC
recording time, and optional calibration ID are mandatory provenance. An
unavailable record contains no guessed matrix. Distortion is explicit and
machine-enforced: `none_v1` requires model `none` with empty order and
coefficients; `opencv_brown_conrady_v1` requires model `brown_conrady` with
`[k1,k2,p1,p2,k3]` and exactly five coefficients; and
`opencv_fisheye_v1` requires model `fisheye` with the exact OpenCV
`[k1,k2,k3,k4]` order and exactly four coefficients. Non-none models always
carry coefficients, and coefficient lists are never interpreted without the
named versioned order.
