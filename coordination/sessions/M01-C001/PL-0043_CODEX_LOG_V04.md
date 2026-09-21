# PL-0043 — Codex Remediation Log V04

Task: PL-0043 — Relationship-aware hosted-XCTest graph guard remediation  
Repository: https://github.com/Sekiph82/PackLab  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V04.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V04.md  
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V03.md

## Synchronization and scope

- Root `TASKS.md` authorized `M01-REMEDIATION-BATCH-003` with Required Actor `CODEX` before material work.
- Synchronized start commit: `eb462f27e08318d5fc8db5865056d8d7d481e3ad`.
- `git fetch origin main --prune`, `git rev-list --left-right --count HEAD...origin/main`, and `git status --porcelain` confirmed a clean `0 0` state before edits.
- No reset, rebase, force-push, destructive checkout, stash, or clean operation was used. `TASKS.md` was not edited and M02 was not started.

## Defect-to-fix mapping

The V03 audit found that the durable Xcode-free guard checked only global presence of the source build-file and target-dependency objects. Removing either graph edge while leaving its standalone object would therefore pass.

The guard now extracts the owning PBX object blocks and proves the relationships directly:

- `PackLabCaptureTests.swift` build-file ID is contained in the `Test Sources` `PBXSourcesBuildPhase` block.
- `PackLabCapture dependency` ID is contained in the `PackLabCaptureTests` `PBXNativeTarget` `dependencies` block.

Two focused mutation tests remove only each relationship while leaving the standalone PBX object declaration intact, assert the mutation occurred, and prove the relationship guard raises `AssertionError`. Existing app testability, test loader/host, source-control signing-boundary, Xcode-free operation, and no-project-rewrite checks remain intact.

## Changed files

- `tests/tools/test_ios_project_graph.py`
- `docs/development/IOS_BASELINE.md`

The correct `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj` was not modified. No adjacent files were required.

## Validation

Expected results: the durable guard must pass the current graph, fail both relationship mutations despite intact standalone objects, run without Xcode, preserve all existing checks, and keep the project itself unchanged. The pre-V04 guard would fail the new mutation assertions because global object presence alone does not prove either edge.

Executed commands and actual results:

- `uv run pytest -q tests/tools/test_ios_project_graph.py` — `3 passed`; the current graph plus both focused mutation proofs passed.
- `uv run pytest -q` — `50 passed, 1 deselected`.
- `uv run ruff check core/src apps/windows-studio/src tools tests` — all checks passed.
- `uv run mypy core/src apps/windows-studio/src tools` — no issues found in 9 source files.
- `git diff --check` — passed.
- `git diff -- TASKS.md` — empty.
- Exact changed-file review — only the two authorized V04 files changed; the Xcode project remained untouched.
- Privacy/security review — no secrets, private scans, supplier files, signing material, caches, or generated artifacts added.

Native `xcodebuild`, simulator, signing, physical-device, and camera execution remain unavailable on this Windows checkout and were not claimed.

## Publication and handoff

- Implementation/evidence commit pushed to `origin/main`: `923a7aefe9db4c10088e873f934b311ea516c159`.
- Post-push `git fetch origin main --prune` completed and divergence was `0 0`.
- This log is published as a separate log-only commit from the implementation/evidence commit.
- No audit verdict is assigned and no future log commit SHA is predeclared.

AWAITING_AUDIT
