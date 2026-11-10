# PL-0427 Codex Prompt V01 — Offline Multi-Ring Capture Recipe

Date: 2026-10-22  
Owner authorization: delegated autonomous queue; PL-0425/0426 are hardware-blocked, so this task is limited to a declarative offline recipe.

## Objective

Add a bounded, deterministic multi-ring capture schedule that can be reviewed/exported before capture. It describes intended object-relative height fractions and azimuths only; it does not control a camera/turntable or claim observed capture metadata.

## Mandatory pre-reads

- PackScan manifest/photo metadata contracts under `core/src/packlab_core/packscan/`
- `core/src/packlab_core/pre_reconstruction_qa.py`
- `coordination/sessions/M19-C007/PL-0425_CODEX_LOG_V01.md`
- `docs/development/NO_ACTIONS_OFFLINE_WORK_POLICY_2026-10-15.md`

## Allowed scope

- Add `core/src/packlab_core/multi_ring_capture_recipe.py` with immutable validated recipe/schedule records.
- Add focused synthetic tests in `tests/core/test_multi_ring_capture_recipe.py`.
- Update root tracker, matching log and local job metadata for local evidence.

## Hard constraints

- Recipe only: no Bluetooth discovery/pairing/commands, camera opening, shutter, motor movement, calibration, capture, PackScan metadata write or network.
- Do not record planned angles as observed angles. Preserve measurement/scale uncertainty and original capture authority.
- Limit ring count, azimuth count, total poses and user inputs. Deterministic pose IDs and order.
- No model/runtime/download, Actions/paid CI, PR, main source push, native build or release claim.

## Validation and handoff

Read required local contracts, run the exact focused local test in `PL-0427_VALIDATION_CRITERIA_V01.md`, run `git diff --check`, and record exact evidence and no-actuation boundaries in `PL-0427_CODEX_LOG_V01.md`. PL-0425/0426 remain blocked until the owner supplies an exact device/protocol and stop-control evidence.
