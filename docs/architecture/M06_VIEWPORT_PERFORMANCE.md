# M06 viewport display budget and benchmark

PL-0157 uses the selected `qt-raster-qimage` adapter and a deterministic
interactive display budget. Authoritative mesh/point-cloud geometry remains in
the scene object; `display_geometry()` returns a separate immutable
representation.

## Policy

- Up to the configured budget is displayed at full source primitive count.
- Larger point clouds use a stable stride (`ceil(source_count / budget)`) and
  retain every `stride`-th point.
- Larger meshes use the same stable stride over triangles and remap only the
  display representation's referenced vertices.
- If a decimator is unavailable, the policy reports `fallback-no-decimator`
  and displays the full source representation rather than silently claiming
  reduced geometry.
- Diagnostics expose source count, display count, stride, budget, level, and
  decimation method.

## Reproduction

```text
QT_QPA_PLATFORM=offscreen uv run --locked python tools/viewport_benchmark.py --output docs/architecture/evidence/M06-viewport-benchmark-v01.json
```

The committed evidence uses deterministic synthetic point clouds and triangle
meshes of 1,000, 10,000, and 50,000 source primitives with a 10,000-point or
triangle display budget. Each case records geometry type, source/display
primitive counts, initialization/setup, display-representation, render and
interaction proxies, image size, source non-mutation, and `tracemalloc` peak
observations plus Python/Qt/platform/backend metadata.

The measurements are local software/offscreen proxies. They do not establish
physical GPU throughput, native-driver performance, or calibrated scan
accuracy. The synthetic fixtures are repository-safe and are not supplier or
private scan data.
