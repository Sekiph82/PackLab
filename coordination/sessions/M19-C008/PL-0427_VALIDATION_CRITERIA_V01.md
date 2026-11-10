# PL-0427 Validation Criteria V01 — Offline Multi-Ring Capture Recipe

1. Recipe uses finite object-relative height fractions and intended azimuths only; it distinguishes planned from observed capture.
2. Bound ring count, azimuth count and total poses; reject unordered/duplicate/invalid fractions and nonfinite offsets.
3. Schedule order and pose IDs are deterministic and stable for the same recipe.
4. Serialization contains only safe recipe fields and pose plan; no paths, image bytes or owner data.
5. No camera/turntable access, Bluetooth, motor actuation, calibration or PackScan writes occur.
6. Exact local validation: `python -m pytest -q tests/core/test_multi_ring_capture_recipe.py` with `PYTHONPATH=core/src`.
7. `git diff --check` passes; no Actions, paid CI, PR, main source push, native build or release claim.
