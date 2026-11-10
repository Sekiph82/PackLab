# Claude implementation log — PL-0426 turntable angle sync prototype (V01)

Date: 2026-11-11. Implementer: Claude Code. This is not a review.

- New `core/src/packlab_core/turntable_sync.py` (contract `packlab.turntable-angle-sync.v1`):
  - `TurntableAngleEvent` (sequence, commanded angle, optional measured angle, source ID).
  - `synchronize_turntable_angles(photos, events, tolerance_deg=0.5)` binds by sequence and emits the per-photo PackScan turntable parameters. It reports unbound photos (no event, multiple events, outside tolerance, with wrap-around error), orphan events and the largest angular gap.
  - `virtual_camera_to_world` computes `R_z(-angle) @ camera_to_world`, the equivalent camera pose when the object rotates.
- `tests/core/test_turntable_sync.py`: 11 synthetic tests, all events labelled `SYNTHETIC-turntable-sim`.
- Feature flag / fallback: the library is pure and only invoked when turntable events exist. The manual and guided-orbit workflows are unchanged.
- Limits:
  - No real turntable or driver exists. PL-0425 stays `BLOCKED_HARDWARE_TARGET_NOT_PRESENT` and needs the owner's turntable make/model and its control protocol.
  - PackScan photos carry no timestamps, so binding is by capture sequence.
  - The matcher still refuses turntable input (`TurntableMatcherUnsupported`). Feeding these virtual poses to reconstruction is future work.
