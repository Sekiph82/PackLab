# PL-0084 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0084 V02/V02/V01.
- Implementation commit: `d814ff5` (`fix(PL-0084): orchestrate AR reset epochs and diagnostics`).

The single shared ARSession owner now records reset reason/epoch and executes explicit reset/remove-anchor run options. Interruption-ended resets use the same owner. `ResetOrchestrationModel` retains accepted capture IDs while invalidating old pose epochs and retaining reset diagnostics; tests cover repeated/user/degraded reset transitions and recovery.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native ARKit/iPhone execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: real ARSession reset execution, user/system/degraded reset reasons, accepted-capture preservation, epoch continuity invalidation, diagnostics, and state-machine coverage.

READY_FOR_INDEPENDENT_AUDIT
