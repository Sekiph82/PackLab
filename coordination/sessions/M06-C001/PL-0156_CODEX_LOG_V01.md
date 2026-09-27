# PL-0156 Codex Evidence Log V01

- Task: PL-0156 — Viewport screenshot/export preview
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0156_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- PL-0155 was validation-green and visible on `origin/main` before this child started.
- Starting commit: `cce06d7556dfe253932388eac5eff8c9fcdfd0c1`.
- Implementation/evidence commit: `fefecddca6f581d545c6a2063fa93699379ca3ef`.
- No reset, rebase, force-push, destructive clean, or stash operation was used.

## Implementation

- Added `ViewportPreviewExporter` and `export_viewport_preview()` using the selected `qt-raster-qimage` adapter.
- Captures the current camera/view into an explicit PNG path and publishes a sidecar containing project/revision, camera, visible object IDs, backend/version, dimensions, and capability metadata.
- Image and sidecar publication are atomic. Existing outputs require explicit overwrite, and any destination under `project_root/raw` is rejected.
- Sidecar metadata contains no source path or raw payload; unavailable backend errors are structured as `ViewportExportError`.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_viewport.py -q` -> `10 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio/viewport_export.py tests/studio/test_viewport.py` -> passed.
- `uv run --locked mypy apps/windows-studio/src/packlab_studio/viewport_export.py apps/windows-studio/src/packlab_studio/viewport.py` -> passed.
- `uv run --locked pytest -q` -> `287 passed, 4 skipped, 1 deselected`, with two pre-existing duplicate-zip warnings.
- `uv run --locked python -m compileall -q apps/windows-studio/src/packlab_studio tests/studio` and `git diff --check` -> passed.

## Negative / boundary / limitation review

- Non-empty image/dimensions, sidecar redaction, atomic overwrite policy, raw-area rejection, and unavailable-backend failure are covered.
- Preview output is audit evidence, not source geometry or measurement authority.
- Native GPU availability remains unclaimed; no M07/M09 implementation, private scan, generated binary, tracker, or audit artifact was changed.

## Publication and handoff

- Implementation commit was pushed to `origin/main`; remote verification matched `fefecddca6f581d545c6a2063fa93699379ca3ef`.
- Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
