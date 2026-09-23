# PL-0075 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0075 V02/V02/V01.
- Implementation commit: `27b59c2` (`fix(PL-0075): require observed white-balance state`).

Added `WhiteBalanceCaptureReading` and `WhiteBalanceCaptureBinding`. Temperature is accepted only when observed and within a finite physical range; the binding remains stabilizing until an explicit lock. The AVFoundation adapter now exposes an observed-temperature readback and keeps the shared configuration coordinator path.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native Xcode/iPhone execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: immediate continuous-to-lock mutation is split into two phases; actual device temperature can be read back; unavailable/invalid readings fail closed; state remains available to the capture control model. Independent Apple-host verification remains for audit.

READY_FOR_INDEPENDENT_AUDIT
