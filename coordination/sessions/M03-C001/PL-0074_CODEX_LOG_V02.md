# PL-0074 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0074 V02/V02/V01.
- Implementation commit: `0341340` (`fix(PL-0074): bind exposure readings to capture state`).

Added `ExposureCaptureReading` and `ExposureCaptureBinding`. Exposure values are validated before acceptance, ISO is represented as an integer, and the binding remains in metering until an explicit lock transition. The physical adapter supports the same two-phase behavior and routes configuration through `CameraDeviceConfigurationCoordinator` when supplied; the selected-camera control model retains exposure state for UI/view-model binding.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native Xcode/iPhone execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: exposure is now bound to a capture-ready reading and explicit state transition; direct configuration has a shared coordinator seam; invalid/non-finite readings fail closed. Independent Apple-host evidence remains for audit.

READY_FOR_INDEPENDENT_AUDIT
