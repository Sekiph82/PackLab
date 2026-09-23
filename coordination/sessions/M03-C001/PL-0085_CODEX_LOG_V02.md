# PL-0085 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0085 V02/V02/V01.
- Implementation commit: `158ff75` (`fix(PL-0085): bind live pose overlay to runtime state`).

The capture root now owns `CaptureRuntimeViewModel`, which reads the shared ARTrackingService snapshot/latest pose and device-health preflight. The debug overlay is driven by that model, displays tracking/epoch/pose orientation/motion when valid, and keeps explicit unavailable labels otherwise. No synthetic transform or motion values are generated. The root also surfaces tracking and health warnings.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native SwiftUI/ARKit execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: hard-coded unavailable overlay removed, live shared service state/pose seam connected, orientation and motion lines added, simulator/unavailable truthfulness retained, and normal/degraded/recovering formatting tests added.

READY_FOR_INDEPENDENT_AUDIT
