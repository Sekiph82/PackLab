# PL-0152 Codex Evidence Log V01

- Task: PL-0152 — Mesh/point-cloud loading and orbit/pan/zoom
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- PL-0151 selected `qt-raster-qimage`; this child uses that one adapter boundary.
- Starting commit: `8498f17e356ef69df8c4257f6ab4e49a73a7ad1e`.
- Implementation/evidence commit: `67a12cbde33bb8933e59a1b66fa7612a5d0d68da`.
- No reset, rebase, force-push, destructive clean, or stash operation was used.

## Implementation

- Added immutable `MeshGeometry` and `PointCloudGeometry` value objects with bounds metadata.
- Added deterministic OBJ, ASCII PLY, XYZ, PTS, and ASCII PCD loaders with structured missing/empty/corrupt/unsupported errors.
- Added `ViewportCamera` with deterministic orbit, pan, zoom, fit-to-view, reset, and serializable state.
- Added `SceneModel`, `ViewportState`, `ViewportService`, and the selected `QtRasterViewportAdapter`; widgets need not call renderer-specific APIs.
- Added a real QImage/QPainter offscreen render smoke path. Source bytes and geometry buffers remain read-only tuples.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_viewport.py -q` -> `3 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio/viewport.py tests/studio/test_viewport.py` -> passed.
- `uv run --locked mypy apps/windows-studio/src/packlab_studio/viewport.py` -> passed.
- `uv run --locked pytest -q` -> `280 passed, 4 skipped, 1 deselected`, with two pre-existing duplicate-zip warnings.
- `uv run --locked python -m compileall -q apps/windows-studio/src/packlab_studio tests/studio` and `git diff --check` -> passed.

## Negative / boundary / limitation review

- Missing, unsupported, empty, malformed and out-of-range triangle inputs are rejected with a typed error code.
- Camera fit/reset and state round-trip are deterministic; no source file is rewritten.
- Rendering evidence is software/offscreen only; no native GPU or calibrated measurement claim is made.
- No M07 reconstruction or M09 measurement work was introduced. Protected tracker/audit artifacts were untouched.

## Publication and handoff

- Implementation commit was pushed to `origin/main`; remote verification matched `67a12cbde33bb8933e59a1b66fa7612a5d0d68da`.
- Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
