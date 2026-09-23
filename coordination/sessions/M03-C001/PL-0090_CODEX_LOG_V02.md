# PL-0090 — Codex Remediation Log V02

- Authorization: M03-BATCH-002 / READY / CODEX; PL-0070 accepted; PL-0068 OWNER_REQUIRED; no M04 work.
- Prompt/criteria/prior audit read: PL-0090 V02/V02/V01.
- Implementation commit: `58acf73` (`fix(PL-0090): discover and resume persisted sessions`).

Added `SessionDiscoveryService` and `SessionResumeCandidate` to enumerate canonical session roots, decode draft/state, validate source identity and reconstruct rejected/replacement/epoch state. `SessionResumeView` presents Resume, Discard, and blocked-corrupt outcomes; the root workflow discovers candidates on launch. `PersistedSessionState` remains backward-compatible with older records while retaining new history fields.

Validation:

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native SwiftUI/filesystem execution is unavailable on this Windows workspace and is not claimed.
- No TASKS/audit edits, secrets, private assets, caches, or signing material.

Prior findings addressed: launch discovery, resume UI, blocked-corrupt handling, persisted history reconstruction, stale/incomplete validation seam, and restart/discovery tests.

READY_FOR_INDEPENDENT_AUDIT
