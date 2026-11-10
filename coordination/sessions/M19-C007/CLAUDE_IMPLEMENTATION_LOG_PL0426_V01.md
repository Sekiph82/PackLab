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

## V02 fixes after `CLAUDE_PEER_REVIEW_PL0426_V01.md` (CHANGES_REQUIRED)

- **P1-1:**
  - Emitted parameters now include the schema-required `angle_unit: deg` and `angle_convention: clockwise_from_reference`. A test validates them against `schemas/packscan/manifest.schema.json`.
  - The convention is now read explicitly as **clockwise as seen from above**. `docs/packscan/manifest-contract.md` now states this; it is the mandatory pre-read that V01 missed.
  - The virtual-camera transform is therefore `R_z(+angle) @ C`; V01's `R_z(-angle)` was mirrored. A test pins the direction: a camera on −Y ends up at +X after 90°.
- **P2-1:** the largest gap uses distinct angles, so {5, 5, 185} gives 180, not 360.
- **P2-2:** this is a **sync report**. The caller writes each bound photo's parameters into that frame's PackScan manifest. The module writes no artifact itself.
- **P2-3:** new tests cover invalid measured angles (NaN, 360, −1, bool), orphan-only incompleteness, frame indices/count and the calibration label on an incomplete set, the tolerance edge (0.5 passes, 0.51 fails), a negative sequence, the tolerance upper bound and −0.0.
- **P3:**
  - the duplicate-ID check is now linear-time;
  - −0.0 is normalised;
  - `virtual_camera_to_world` rejects non-rigid matrices and documents the z-up station frame (ARKit y-up poses must be converted first).
- **Fallback:** nothing calls this library yet, so the manual and guided-orbit workflows are the default.
