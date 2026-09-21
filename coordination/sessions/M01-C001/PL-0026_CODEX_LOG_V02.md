# PL-0026 Codex Remediation Log V02

- Cycle: M01-C001
- Task: PL-0026 — Windows cache/data ownership remediation
- Prior audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_V01.md
- Remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V02.md
- Remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_CRITERIA_V02.md
- Synchronized start: `7ce428564ef069d86275b77b503435f2977a8e14`; `HEAD...origin/main` was `0 0`.
- Implementation/evidence commit: `c485f0158e930ee3c117f8a98f932d2fd720b785`

## Defect-to-fix mapping

The V01 audit found that the Windows default cache root was `%LOCALAPPDATA%/PackLab` while durable project data was `%LOCALAPPDATA%/PackLab/data`, placing owner data beneath the logical cache root. The remediation changes the Windows defaults to sibling roots: cache `%LOCALAPPDATA%/PackLab/cache`, temporary workspace `%LOCALAPPDATA%/PackLab/cache/work`, and durable project data `%LOCALAPPDATA%/PackLab/data`.

macOS/Linux defaults, explicit `PACKLAB_CACHE_ROOT` and `PACKLAB_DATA_ROOT` overrides, lazy creation, and no automatic deletion are preserved. The policy documentation now states the exact sibling semantics.

## Changed files

- `core/src/packlab_core/cache_paths.py`
- `tests/core/test_cache_paths.py`
- `docs/development/CACHE_POLICY.md`

## Validation

Expected results and failure conditions:

- `uv run pytest -q tests/core/test_cache_paths.py` — expected deterministic platform/override/lazy-creation and Windows sibling-boundary tests to pass. Initial actual: `1 failed, 3 passed` because the existing Windows expected default still named the old cache path; after updating that expectation, actual: `4 passed`.
- `uv run pytest -q` — expected sibling M01 regression suite to remain green. Actual: `33 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — expected no diagnostics. Actual: all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — expected no type errors. Actual: `Success: no issues found in 9 source files`.
- `git diff --check` — expected no whitespace errors. Actual: passed.
- `git diff -- TASKS.md` — expected empty. Actual: empty.
- Exact changed-file review — expected only three authorized files. Actual: only those three files changed.
- Protected/privacy review — expected temporary-path tests only and no private data/secrets/cache artifacts. Actual: passed; all test filesystem operations use `tmp_path`.

The new regression proves Windows project data is neither equal to nor a descendant of cache and that the roots are siblings. It would fail against the audited pre-remediation layout.

## Scope and platform limitations

Only the authorized PL-0026 source, tests, and policy changed. No M02 work, tracker edit, automatic deletion, or real user-profile directory was used. No native/device evidence was required or fabricated.

## Remote evidence and handoff

Implementation push completed. The first post-push fetch encountered a transient DNS resolution error; a retry succeeded. Final fetch verified `HEAD` and `origin/main` both resolve to `c485f0158e930ee3c117f8a98f932d2fd720b785` with divergence `0 0`.

AWAITING_AUDIT
