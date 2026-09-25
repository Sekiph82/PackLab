# PL-0135 Codex Evidence Log V01

- Task: PL-0135 — PySide6 application shell
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- Authorization was verified in root `TASKS.md`: M06-BATCH-001 / READY / CODEX; M03–M05 accepted; PL-0068 remains OWNER_REQUIRED; M07 not started.
- Synchronized starting commit: `6ac8c090dc61f43635e1a4ff64abcfb317b79d98`.
- `git fetch origin main --prune`, `git rev-list --left-right --count HEAD...origin/main` returned `0 0` after the permitted fast-forward, and `git status --porcelain` was clean before edits.
- `TASKS.md` and all ChatGPT audit artifacts were unchanged.
- No reset, rebase, force-push, destructive checkout, stash, or clean operation was used.

## Files and implementation

- `pyproject.toml`: declares `PySide6>=6.8,<7` for Python 3.12.
- `uv.lock`: reproducibly locks PySide6 6.11.2 and its Qt/Shiboken runtime packages.
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`: records the selected PySide6 presentation boundary and licensing attention.
- `apps/windows-studio/src/packlab_studio/app.py`: owns the single QApplication, organization/application identifiers, import-safe entry point, exception boundary and deterministic startup failure code.
- `apps/windows-studio/src/packlab_studio/shell.py`: provides the single production QMainWindow with object identity, title, icon hook and clean-close behavior.
- `tests/studio/test_shell.py`: exercises import-time QApplication absence, offscreen application construction, one-window identity and close processing.

## Validation evidence

Expected result for each check was exit code 0; any non-zero exit would have stopped publication.

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_shell.py -q` -> `2 passed`.
- `uv run --locked pytest -q` -> `221 passed, 4 skipped, 1 deselected` (two existing zipfile warnings only).
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio/test_shell.py` -> passed.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` -> passed.
- `git diff --check` and staged `git diff --cached --check` -> passed.

The test used the production `create_application` and `StudioMainWindow` seams, with no internet, physical display or GPU requirement. PySide6 was installed only through the locked project environment; no untracked pip installation was used.

## Commit and publication evidence

- Implementation/evidence commit: `a244180af73c74c76910c10f2814bc47d2e857b7`.
- `git push origin main` succeeded.
- `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` both returned `a244180af73c74c76910c10f2814bc47d2e857b7` before this log-only commit.
- Known limitation: native Windows display, packaging and GPU behavior were not claimed; this child used deterministic offscreen Qt evidence.
- Secrets/privacy/signing/generated-file review: no credentials, tokens, private scans, signing material or generated runtime artifacts were added.

## Handoff

This is builder evidence only. Independent ChatGPT audit remains required; no acceptance verdict is assigned here.

READY_FOR_INDEPENDENT_AUDIT
