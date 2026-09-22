# Synthetic calibration ground truth

PL-0067 uses deterministic synthetic marker observations so PackLab can test
calibration math without private images, camera access, printed mats, or owner
device evidence.

## Generator parameters

- marker dictionary semantics: PackLab AprilTag policy IDs, represented as
  detection-style `MarkerObservation` records;
- corner unit: image pixels;
- corner order: top-left, top-right, bottom-right, bottom-left;
- ground-truth marker side: `40 mm`;
- ground-truth scale: `0.4 mm/px`, therefore an ideal `40 mm` marker has
  `100 px` edge length;
- image coordinate convention: `x` right, `y` down;
- deterministic perturbations: per-marker pixel side changes, rejected/partial
  observations, degenerate zero-size geometry, inconsistent marker scale,
  wrong real-world units, and intentionally bad corner ordering.

The synthetic records include provenance strings naming the generator version
and scenario. These records are regression fixtures in code, not physical
measurements.

## Expected bounds

Ideal cases must recover `0.4 mm/px` exactly within floating-point tolerance.
Noisy cases must remain within `0.005 mm/px` of ground truth and produce a
usable confidence status. Inconsistent, degenerate, and malformed-order cases
must fail closed through scale or confidence rejection.

These tests are sensitivity-bearing: they assert numeric ground truth, unit
semantics, and corner-order behavior so changes that invert scale math, drift
from millimetres, or ignore ordered corners fail the suite.
