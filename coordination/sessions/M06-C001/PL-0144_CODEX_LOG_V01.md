# PL-0144 Codex Evidence Log V01

- Task: PL-0144 — New/Open/Close project lifecycle
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0144_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0144_CHATGPT_AUDIT_CRITERIA_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- M06-BATCH-001 / READY / CODEX authorization was rechecked; `TASKS.md`, ChatGPT audit artifacts, M03–M05, PL-0068 and M07 were preserved.
- Synchronized child start commit: `7831bc1012622167af1b75200e8a1b543f0bb3f1`.
- Implementation commit: `7783019412218140f3cc1a0f4f31e9fce6f16aba`.
- No reset, rebase, force-push, clean or stash operation was used.

## Implementation

- `project.py` defines one `ProjectManager`, validated portable `ProjectMetadata`, atomic staged project creation, open validation, close-without-delete and project switching.
- New projects create layout and metadata in a staging directory before atomic publication; duplicate/non-empty destinations and corrupt layouts/metadata fail cleanly.
- Active jobs block close unless the caller explicitly supplies the close policy; shell navigation context references the manager rather than widget-local project state.
- `test_project.py` covers create/open/close, identity-preserving reopen, switching, duplicate/corrupt/partial failure, active-job policy and shell context composition.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio -q` -> `30 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio` -> passed.
- Targeted mypy for project/shell -> passed.
- `uv run --locked pytest -q` -> `249 passed, 4 skipped, 1 deselected`; only two existing zipfile warnings.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` and `git diff --check` -> passed.

## Publication and limitations

- Implementation commit was pushed to `origin/main`; remote verification matched `7783019412218140f3cc1a0f4f31e9fce6f16aba` before this log-only commit.
- Project lifecycle does not delete or mutate raw evidence and does not claim reconstruction or calibrated measurement behavior.
- Secrets/privacy/signing/generated-file review was clean.

## Handoff

Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
