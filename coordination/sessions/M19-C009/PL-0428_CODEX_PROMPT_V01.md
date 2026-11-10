# PL-0428 Codex Prompt V01 — Adaptive Angle-Density Plan

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; offline declarative planning follows PL-0427 and does not depend on hardware actuation.

## Objective

Create a deterministic plan that allocates a bounded number of intended camera azimuth samples to angular geometry sectors using digest-bound normalized sector-complexity evidence.

## Mandatory pre-reads

- `core/src/packlab_core/multi_ring_capture_recipe.py`
- `core/src/packlab_core/geometry_statistics.py`
- `core/src/packlab_core/reconstruction_anomaly.py`
- `coordination/sessions/M19-C008/PL-0427_CODEX_PROMPT_V01.md`
- `coordination/sessions/M19-C008/PL-0427_VALIDATION_CRITERIA_V01.md`
- `docs/development/NO_ACTIONS_OFFLINE_WORK_POLICY_2026-10-15.md`

## Allowed scope

- Add `core/src/packlab_core/adaptive_angle_plan.py` with validated complexity evidence, bounded policy and deterministic planned azimuths.
- Add focused synthetic tests in `tests/core/test_adaptive_angle_plan.py`.
- Update `TASKS.md`, matching log and local job metadata.

## Hard constraints

- The caller-supplied sector score is an untrusted normalized proposal input pinned to a geometry revision and digest; do not claim this module computes or validates geometric complexity.
- Plan only. No Bluetooth, turntable/camera, image, PackScan write, motor command, physical calibration or observed-angle claim.
- Require exact gap-free sector coverage of `[0,360]`, finite score bounds, deterministic ordering, and hard upper limits on sector/sample counts.
- No raw geometry, paths or owner data in serialized output. No model/SDK/checkpoint or inference.
- Zero Actions/paid CI, no PR, no main source push, no native build or release claim.

## Validation and handoff

Read required references, run the exact focused local test in `PL-0428_VALIDATION_CRITERIA_V01.md` using the project `.venv`, then `git diff --check`. Record local results and all no-actuation limitations in `PL-0428_CODEX_LOG_V01.md`. PL-0425/0426 remain hardware-blocked.
