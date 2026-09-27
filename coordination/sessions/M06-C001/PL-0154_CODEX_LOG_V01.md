# PL-0154 Codex Evidence Log V01

- Task: PL-0154 — Object selection and visibility model
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0154_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- PL-0153 was validation-green and visible on `origin/main` before this child started.
- Starting commit: `34e818a4aead0241a1a3f8ad669e0d29da9cb5b9`.
- Implementation/evidence commit: `59c7d0d706a156981ff7beeca48fcbe07a487427`.
- No reset, rebase, force-push, destructive clean, or stash operation was used.

## Implementation

- Added stable `SceneObjectId` and `SceneObjectKind` values for Scan Mesh, Design Model, cap, label, and reference geometry.
- `SceneModel` owns registration, duplicate-ID rejection, single selection, clear/select behavior, visibility changes, and hidden/missing selection clearing.
- `ViewportService` exposes the scene snapshot as an object-tree/inspector seam and keeps `ViewportState` synchronized with scene truth.
- Scene object metadata is serializable without serializing or mutating source geometry.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_viewport.py -q` -> `7 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio/viewport.py tests/studio/test_viewport.py` -> passed.
- `uv run --locked mypy apps/windows-studio/src/packlab_studio/viewport.py` -> passed.
- `uv run --locked pytest -q` -> `284 passed, 4 skipped, 1 deselected`, with two pre-existing duplicate-zip warnings.
- `uv run --locked python -m compileall -q apps/windows-studio/src/packlab_studio tests/studio` and `git diff --check` -> passed.

## Negative / boundary / limitation review

- Duplicate IDs are rejected; hidden or missing selection clears deterministically; visibility restore is covered.
- Raw source files and geometry buffers remain unchanged.
- Rendering remains software/offscreen and no native GPU or calibrated measurement claim was made.
- Root `TASKS.md`, ChatGPT audit/criteria artifacts, accepted foundation, M07, and M09 work were untouched.

## Publication and handoff

- Implementation commit was pushed to `origin/main`; remote verification matched `59c7d0d706a156981ff7beeca48fcbe07a487427`.
- Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
