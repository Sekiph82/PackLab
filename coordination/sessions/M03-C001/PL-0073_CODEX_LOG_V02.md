# PL-0073 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0073 V02/V02/V01.
- Implementation commit: `64ef55f` (`fix(PL-0073): serialize selected-camera focus configuration`).

The remediation adds `CameraDeviceConfigurationCoordinator` as the selected-device lock owner, verifies the selected main rear wide lens identity, and routes focus configuration through that coordinator when supplied. Focus configuration is now explicitly two phase: continuous focus first, then a separate lock operation after stabilization. `CameraCaptureControlModel` exposes selected-lens and focus/exposure/white-balance state for the capture view model. Existing policy behavior remains intact and has a new independent state-retention test.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native Xcode/iPhone execution is unavailable on this Windows workspace and is not claimed.
- `TASKS.md` and ChatGPT audits were not edited; privacy/signing review found no secrets or private assets.

Prior findings addressed: selected-camera binding and shared serialized configuration path are implemented; immediate focus lock is separated from continuous stabilization; UI/view-model state has an explicit model seam. Independent Apple-host verification remains for audit.

READY_FOR_INDEPENDENT_AUDIT
