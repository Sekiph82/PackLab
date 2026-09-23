# PL-0072 — Codex Remediation Log V02

## Scope and authorization

- Authorized batch: `M03-BATCH-002`, READY, CODEX.
- Scope: PL-0072 only; PL-0070 remains accepted, PL-0068 remains OWNER_REQUIRED, and no M04 work was started.
- Prompt/criteria read: `PL-0072_CODEX_PROMPT_V02.md`, `PL-0072_CHATGPT_AUDIT_CRITERIA_V02.md`, and prior independent audit V01.

## Implementation

- Implementation commit: `882d386` (`fix(PL-0072): persist immutable original source records`).
- Added `OriginalSourceStore`, an actor that validates digest/dimensions, atomically writes the immutable original and its source record, refuses conflicting overwrite, and supports reopen/load.
- The source record and bytes remain separate from derivative paths; failed record writes remove only the newly-created source.
- Added filesystem behavior coverage for persistence, reopen, idempotent same-content persistence, and digest mismatch.

## Validation

- `git diff --check`: passed.
- `$env:PYTHONPATH=(Join-Path (Get-Location) 'core/src'); python -m pytest -q`: `162 passed, 4 skipped, 1 deselected, 1 warning`.
- Native Xcode/iPhone execution: unavailable on this Windows workspace; not claimed.
- Protected-file/privacy/signing review: `TASKS.md` and ChatGPT audits untouched; no secrets/private assets/caches/signing material added.

## Prior finding mapping

- Source persistence: fixed by `OriginalSourceStore.persist` and `load`.
- Immutable overwrite protection: same digest is idempotent; conflicting bytes fail closed.
- Derivative separation: `SourceIntegrity.derivativePath` remains outside the immutable source root.

READY_FOR_INDEPENDENT_AUDIT
