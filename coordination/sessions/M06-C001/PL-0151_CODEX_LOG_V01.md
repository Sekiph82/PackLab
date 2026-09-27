# PL-0151 Codex Evidence Log V01

- Task: PL-0151 — 3D viewport technology performance spike
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C002/MASTER_CODEX_PROMPT_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- PL-0150 was validation-green and its implementation/log commits were visible before this child started.
- Starting commit: `2086a6249471433659d4bad994f86cdd7a84fdc1`.
- Implementation/evidence commit: `fd79ea18693c1099003772467ce814b9d09ac26f`.
- No reset, rebase, force-push, destructive clean, or stash operation was used.

## Decision and evidence

- Compared `qt-raster-qimage` and `qt-opengl-offscreen` using executable PySide6 probes on Python 3.12 / Qt 6.11.2 / Windows 11 with `QT_QPA_PLATFORM=offscreen`.
- The raster candidate executed deterministic 1,000 / 10,000 / 50,000 point render proxies. Recorded evidence is at https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/evidence/M06-viewport-spike-v01.json.
- The OpenGL candidate executed an offscreen context probe; this host did not expose a usable context. No physical GPU/native performance claim was made.
- Selected `qt-raster-qimage` in https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0002-m06-viewport-backend.md because it is deterministic, headless-capable, Windows-compatible, and requires no new dependency. Future viewport code must use the PackLab adapter boundary.
- Existing locked `PySide6>=6.8,<7` remains the only selected viewport dependency; no dependency or license change was introduced.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_viewport_spike.py -q` -> `1 passed`.
- `QT_QPA_PLATFORM=offscreen uv run --locked python tools/viewport_spike.py --output docs/architecture/evidence/M06-viewport-spike-v01.json` -> passed and wrote the small evidence artifact.
- `uv run --locked ruff check tools/viewport_spike.py tests/studio/test_viewport_spike.py` -> passed.
- `uv run --locked mypy tools/viewport_spike.py` -> passed.
- `uv run --locked pytest -q` -> `277 passed, 4 skipped, 1 deselected`, with two pre-existing duplicate-zip warnings.
- `uv run --locked python -m compileall -q tools/viewport_spike.py apps/windows-studio/src/packlab_studio` and `git diff --check` -> passed.

## Limitations / scope review

- The evidence is software/offscreen and host-specific; it is not a physical GPU, driver, or native-window benchmark.
- No M07 reconstruction, M09 calibrated measurement accuracy, source geometry, private scans, or generated binaries were added.
- Root `TASKS.md` and ChatGPT audit/criteria artifacts were untouched.

## Publication and handoff

- Implementation commit was pushed to `origin/main`; remote verification matched `fd79ea18693c1099003772467ce814b9d09ac26f`.
- Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
