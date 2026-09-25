# PL-0136 Codex Evidence Log V01

- Task: PL-0136 — Main navigation
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0136_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0136_CHATGPT_AUDIT_CRITERIA_V01.md
- Repository: https://github.com/Sekiph82/PackLab
- Branch: `main`

## Scope and synchronization

- M06-BATCH-001 / READY / CODEX authorization and the protected tracker state were rechecked before implementation; M07 was not started.
- Synchronized child start commit: `9da2a411fe17a3b438b27ac579ca0936b3aad925`.
- The implementation was published at `26bf62f9314136248dcde5bffb78d26bd53a05a0`. A test-isolation correction was required by the aggregate run and was published as `c1916e51dbc7475d9897642fb322692f8eb427a5` before this log.
- `TASKS.md` and ChatGPT audit artifacts were not edited. No reset, rebase, force-push, clean or stash was used.

## Implementation

- `navigation.py` defines stable `Route` IDs, `NavigationController`, deterministic project context, the route list panel and one stacked route surface.
- `shell.py` now composes one `QMainWindow` with the central navigation panel and route stack for Library, Capture Inbox, Reconstruction, Editor and Settings.
- Capture Inbox accepts the existing M05 `IngestController` and receiver instances through dependency injection; no ingest/validation/raw-store logic was duplicated.
- `test_navigation.py` covers every transition, unknown-route rejection, current-route retention and production-shell Capture Inbox composition.
- `test_shell.py` now verifies import-time QApplication absence in a fresh subprocess so the assertion is independent of test order.

## Validation evidence

- `QT_QPA_PLATFORM=offscreen uv run --locked pytest tests/studio/test_shell.py tests/studio/test_navigation.py -q` -> `5 passed`.
- `uv run --locked ruff check apps/windows-studio/src/packlab_studio tests/studio` -> passed.
- Targeted `uv run --locked mypy ...app.py ...shell.py ...navigation.py` -> passed.
- `uv run --locked pytest -q` -> `224 passed, 4 skipped, 1 deselected`; only two pre-existing zipfile warnings.
- `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests/studio` and `git diff --check` -> passed.
- The first aggregate run found the test-order defect (`1 failed`); it was corrected and the exact suite was rerun successfully. This is recorded rather than hidden.

## Publication and limitations

- `git push origin main` succeeded for both implementation commits and `git ls-remote origin refs/heads/main` matched `c1916e51dbc7475d9897642fb322692f8eb427a5`.
- No native/GPU/display claim was made; UI checks were offscreen and deterministic.
- Secrets/privacy/signing/generated-file review was clean. Raw M05 evidence was not accessed or mutated.

## Handoff

Builder evidence only; independent ChatGPT audit remains required.

READY_FOR_INDEPENDENT_AUDIT
