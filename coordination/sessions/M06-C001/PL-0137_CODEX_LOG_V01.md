# PL-0137 Codex Evidence Log V01

- Task: PL-0137 — Dockable logical workspace layout
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CHATGPT_AUDIT_CRITERIA_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- The M06-BATCH-001 / READY / CODEX authorization was rechecked; `TASKS.md`, M03–M05 state, PL-0068 and M07 were preserved.
- Synchronized child start commit: `5747d2368d8eae4128d7f9d09685cc9245448eaf`.
- Implementation commits: `80c9d16083f5c49b370a89713b60192f068c568c` and the required whitespace correction `106b88f8dea57c8f4ee4787d3eba53f491137746`.
- No reset, rebase, force-push, clean, stash or protected-file edit was used.

## Implementation

- `workspace.py` owns four stable dock IDs for scene/object tree, properties/inspector, jobs/activity and logs.
- One dock instance is created per ID, with stable `objectName` values and all docking constrained to valid left/right/bottom areas.
- Per-workspace defaults for Library, Capture Inbox and Settings are deterministic, route-independent, and reset through one manager.
- `shell.py` composes `WorkspaceManager` into the existing single QMainWindow.
- `test_workspace.py` covers inventory, unique stable names, show/hide state, default reset and no duplicate dock construction.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio -q` -> `7 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio` -> passed.
- Targeted mypy for the Studio shell/navigation/workspace modules -> passed.
- `uv run --locked pytest -q` -> `226 passed, 4 skipped, 1 deselected`; only two existing zipfile warnings.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` and `git diff --check` -> passed.
- The initial staged check found one extra blank line at EOF; it was corrected in `106b88f8dea57c8f4ee4787d3eba53f491137746` and the checks were rerun.

## Publication and limitations

- Both implementation commits and the log publication were pushed to `origin/main`; remote verification is recorded after publication.
- `git rev-parse HEAD` and `git ls-remote origin refs/heads/main` matched `106b88f8dea57c8f4ee4787d3eba53f491137746` before the log-only commit.
- No GPU/native claim was made; the UI evidence was offscreen.
- No M05 raw evidence or private data was accessed or changed; secrets/privacy/signing/generated-file review was clean.

## Handoff

Builder evidence only. Independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
