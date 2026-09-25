# PL-0138 Codex Evidence Log V01

- Task: PL-0138 — Persistent window/workspace preferences
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CHATGPT_AUDIT_CRITERIA_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- M06-BATCH-001 / READY / CODEX authorization was rechecked; `TASKS.md`, ChatGPT audit artifacts, accepted M03–M05 state, PL-0068 and M07 were preserved.
- Synchronized child start commit: `de90f7e724c6d50434f9a670075ec4412e030188`.
- Implementation commit: `7a2822b0d815972c0f1f3a8af68a386088e98a61`.
- No reset, rebase, force-push, clean or stash operation was used.

## Implementation

- `preferences.py` defines a schema-versioned `WindowPreferences` record and injectable `PreferencesStore`.
- Preferences are atomically written through a flushed/fsynced temporary file and replace; corrupt, future and legacy v0 state safely defaults or migrates.
- Geometry is bounded and optionally clamped to available desktop bounds. Only UI state is stored: geometry, maximized/fullscreen flags, dock state, route, theme and display scale.
- `shell.py` restores and persists route, dock layout and window state through the injected store without storing project payloads or secrets.
- `test_preferences.py` covers round-trip/atomic cleanup, corrupt/future fallback, v0 migration, geometry sanitization and production-shell restore.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio -q` -> `11 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio` -> passed.
- Targeted mypy for the Studio app/shell/navigation/workspace/preferences modules -> passed.
- `uv run --locked pytest -q` -> `230 passed, 4 skipped, 1 deselected`; only two existing zipfile warnings.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` and `git diff --check` -> passed.
- A first implementation check caught PySide6 type/import issues during development; they were corrected before the implementation commit and the full checks above were rerun.

## Publication and limitations

- `git push origin main` succeeded; `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` matched `7a2822b0d815972c0f1f3a8af68a386088e98a61` before this log-only commit.
- Offscreen Qt was used; no native/GPU performance claim was made.
- Secrets/privacy/signing/generated-file review was clean; raw M05 evidence is not part of preferences.

## Handoff

Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
