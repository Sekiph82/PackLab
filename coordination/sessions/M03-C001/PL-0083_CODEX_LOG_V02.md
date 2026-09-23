# PL-0083 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0083 V02/V02/V01.
- Implementation commit: `0d055ea` (`fix(PL-0083): add tracking recovery hysteresis`).

Added `TrackingRecoveryPolicy` with configurable sustained-normal frame threshold, explicit recovering state during stabilization, retained `TrackingDiagnosticEvent` history, and `TrackingWarningViewModel` for visible capture warnings. Rapid flapping cannot immediately clear the warning; pose eligibility returns only after the required stable normal frames. Existing stateless classifier behavior is preserved.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native UI/AR execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: visible-warning view-model seam, recovery hysteresis, retained diagnostics, flapping/stability tests, and explicit unavailable/degraded messaging.

READY_FOR_INDEPENDENT_AUDIT
