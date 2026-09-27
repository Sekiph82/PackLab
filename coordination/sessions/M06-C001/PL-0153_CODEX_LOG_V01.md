# PL-0153 Codex Evidence Log V01

- Task: PL-0153 — World grid, axes and millimetre scale cues
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0153_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- PL-0152 was validation-green and visible on `origin/main` before this child started.
- Starting commit: `02a11d7d0d006563fb06740df8a5c0f55afb6a25`.
- Implementation/evidence commit: `89eeaef7c2586c133020484ff528a65d4deda9b5`.
- No reset, rebase, force-push, destructive clean, or stash operation was used.

## Implementation

- Added backend-independent `GridSpec`, `grid_spec()` and stable right-handed `axis_metadata()` to the viewport state seam.
- Grid spacing adapts deterministically through 1/2/5 decade thresholds from camera distance while retaining millimetre metadata; source coordinates are never rescaled.
- Grid, axes, and visual scale-cue visibility are persisted through `ViewportState` and restored by `ViewportService`.
- The offscreen raster adapter renders the line-based cues; text-raster plugin availability is not assumed, and the grid specification remains available for UI labels/inspector consumers.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_viewport.py -q` -> `5 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio/viewport.py tests/studio/test_viewport.py` -> passed.
- `uv run --locked mypy apps/windows-studio/src/packlab_studio/viewport.py` -> passed.
- `uv run --locked pytest -q` -> `282 passed, 4 skipped, 1 deselected`, with two pre-existing duplicate-zip warnings.
- `uv run --locked python -m compileall -q apps/windows-studio/src/packlab_studio tests/studio` and `git diff --check` -> passed.

## Failure / limitation review

- An initial offscreen Qt text-raster path terminated the native test process; it was removed from the renderer and the deterministic metadata/state seam retained. The corrected focused and full suites passed.
- The grid is a visual unit cue only. No calibrated physical measurement accuracy or GPU/native performance claim was made; M09 owns measurement accuracy.
- Root `TASKS.md`, ChatGPT audit/criteria artifacts, raw source geometry, M07, and later-milestone work were untouched.

## Publication and handoff

- Implementation commit was pushed to `origin/main`; remote verification matched `89eeaef7c2586c133020484ff528a65d4deda9b5`.
- Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
