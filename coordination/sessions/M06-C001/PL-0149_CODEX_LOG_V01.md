# PL-0149 Codex Evidence Log V01

- Task: PL-0149 — Derived-artifact invalidation
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0149_CHATGPT_AUDIT_CRITERIA_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- M06-BATCH-001 / READY / CODEX was rechecked; protected tracker/audit artifacts, M03–M05, PL-0068 and M07 were preserved.
- Synchronized child start commit: `07207e5df4f5ae4acbcd4a2a25616cf6a4709bf7`.
- Implementation commits: `dd96f6e78e744195b8e82703e0b17814cd5ca2eb` and whitespace correction `0442a3fea64d5133f9ccdac788444fbe0407caf4`.
- No reset, rebase, force-push, clean or stash operation was used.

## Implementation

- `provenance.py` stores versioned derived-artifact records with upstream IDs, input digests, parameter digest, project revision and status.
- Invalidation propagates deterministically from changed inputs/parameters through transitive upstream dependencies; unrelated artifacts remain fresh.
- Integrity refresh detects missing/tampered source inputs as invalid and persists status atomically. Raw data is never deleted or rewritten.
- `test_provenance.py` covers direct/transitive invalidation, unrelated changes, parameter changes, tampered input detection and raw non-mutation.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio -q` -> `43 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio` -> passed.
- Targeted mypy for `provenance.py` -> passed.
- `uv run --locked pytest -q` -> `262 passed, 4 skipped, 1 deselected`; only two existing zipfile warnings.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` and `git diff --check` -> passed.
- Two EOF blank-line issues were caught by staged checking and corrected before handoff.

## Publication and limitations

- Implementation commits were pushed to `origin/main`; remote verification matched `0442a3fea64d5133f9ccdac788444fbe0407caf4` before this log-only commit.
- Provenance is local project evidence; no reconstruction engine, native/GPU or calibrated measurement claim was made.
- Secrets/privacy/signing/generated-file review was clean and raw evidence remained unchanged.

## Handoff

Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
