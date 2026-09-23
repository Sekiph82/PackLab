# PL-0081 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0081 V02/V02/V01.
- Implementation commit: `8250f57` (`fix(PL-0081): put CoreMotion behind service seam`).

Added explicit `MotionServiceState` and a physical `CoreMotionMotionService` behind the existing seam, including unavailable/start/update failure states. Simulator fallback now reports unavailable and never creates evidence. Motion samples remain bounded, reject malformed/non-finite data, and `MotionAligner` binds nearest eligible samples with explicit available/stale/unavailable status and delta.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native CoreMotion/iPhone execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: existing MotionService seam, truthful provider failures, bounded timestamp-domain buffering, accepted-capture alignment, stale/missing handling, and provider-failure test seams.

READY_FOR_INDEPENDENT_AUDIT
