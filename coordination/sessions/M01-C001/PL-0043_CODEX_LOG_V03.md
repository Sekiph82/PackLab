# PL-0043 — Codex Remediation Log V03

Task: PL-0043 — Durable hosted-XCTest graph regression remediation  
Repository: https://github.com/Sekiph82/PackLab  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V03.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V03.md  
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V02.md

## Synchronization and scope

- Root `TASKS.md` authorized `M01-REMEDIATION-BATCH-002` with Required Actor `CODEX` before material work.
- Synchronized start commit: `316b1110e31e0ecb588a008fd4e92fa80fc3f02e`.
- `git fetch origin main --prune`, `git rev-list --left-right --count HEAD...origin/main`, and `git status --porcelain` confirmed a clean `0 0` state before edits.
- No reset, rebase, force-push, destructive checkout, stash, or clean operation was used. `TASKS.md` was not edited and M02 was not started.

## Defect-to-fix mapping

The V02 audit found that the hosted XCTest graph was repaired but protected only by one-off local assertions. The Xcode project was not rewritten. Instead, `tests/tools/test_ios_project_graph.py` now provides a durable Xcode-free regression that reads the source-controlled `project.pbxproj` and asserts:

- app Debug and Release `ENABLE_TESTABILITY = YES`;
- test Debug and Release `BUNDLE_LOADER = "$(BUILT_PRODUCTS_DIR)/PackLabCapture.app/PackLabCapture"`;
- `TEST_HOST = "$(BUNDLE_LOADER)"`;
- PackLabCaptureTests source membership and dependency on PackLabCapture;
- absence of personal `DEVELOPMENT_TEAM`, `CODE_SIGN_IDENTITY`, and provisioning-profile settings.

The iOS baseline documentation identifies the durable regression and preserves the explicit Windows/static versus future macOS/Xcode evidence boundary.

## Changed files

- `tests/tools/test_ios_project_graph.py`
- `docs/development/IOS_BASELINE.md`

The now-correct Xcode project was not changed. No adjacent files were required.

## Validation

Expected results: the durable test must pass on Windows/Linux without Xcode, fail against the pre-remediation graph if testability/host/source/dependency/signing invariants regress, and preserve the existing project graph. A missing testability, loader, host, source, dependency, or signing guard would fail the test.

Executed commands and actual results:

- `uv run pytest -q tests/tools/test_ios_project_graph.py` — `1 passed`.
- `uv run pytest -q` — `48 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — no issues found in 9 source files.
- `git diff --check` — passed.
- `git diff -- TASKS.md` — empty.
- Exact changed-file review — only the two authorized files changed; the Xcode graph itself remained untouched.
- Privacy/security review — no secrets, private scans, supplier files, signing material, caches, or generated artifacts added.

Native `xcodebuild`, simulator, signing, physical-device, and camera execution remain unavailable on this Windows checkout and were not claimed.

## Publication and handoff

- Implementation/evidence commit pushed to `origin/main`: `84d9c3e64e646ccf5320617070e40b4aa112e244`.
- Post-push `git fetch origin main --prune` completed and divergence was `0 0`.
- This log is published as a separate log-only commit from the implementation/evidence commit.
- No audit verdict is assigned and no future log commit SHA is predeclared.

AWAITING_AUDIT
