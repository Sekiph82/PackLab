# PL-0043 — Codex Remediation Work Order V04

Task: **PL-0043 — Relationship-aware hosted-XCTest graph guard remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V04.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V04.md

## Gate

Read AGENTS.md, TASKS.md, the blocking audit, this prompt and its criteria. TASKS.md must authorize `M01-REMEDIATION-BATCH-003` with Required Actor `CODEX`.

Before material work:
```
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git status --porcelain
```

Require a safe synchronized state. Never reset, rebase, force-push, destructively clean, stash owner work, edit TASKS.md, or start M02.

## Authorized files

- `tests/tools/test_ios_project_graph.py`
- `docs/development/IOS_BASELINE.md` only if wording must be aligned with the strengthened regression

Do **not** modify the now-correct Xcode project merely to manufacture a diff.

## Mandatory requirements

1. Preserve all existing valid checks for app `ENABLE_TESTABILITY`, test `BUNDLE_LOADER`, `TEST_HOST=$(BUNDLE_LOADER)`, and absence of personal signing/provisioning settings.
2. Replace unconstrained whole-file presence checks for test-source membership and app-target dependency with relationship-aware assertions.
3. Prove the `PackLabCaptureTests.swift` build-file ID is actually contained in the `Test Sources` PBXSourcesBuildPhase.
4. Prove the `PackLabCapture dependency` ID is actually contained in the `PackLabCaptureTests` PBXNativeTarget `dependencies` block.
5. Add focused mutation/helper tests proving that leaving the standalone PBXBuildFile/PBXTargetDependency objects in place while removing either relationship causes the guard to fail.
6. Keep the test Xcode-free and runnable in the normal pytest suite on Windows/Linux.
7. Do not claim xcodebuild, simulator, signing, physical-device or camera execution.
8. Preserve all accepted M01 behavior and no-personal-signing boundaries.

## Validation

Run the focused graph regression, its mutation/helper coverage, full Python regression, Ruff, mypy, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, protected-file review and privacy/secrets review.

The focused evidence must demonstrate failure for both relationship mutations, not merely state that it would fail.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V04.md with synchronized start, implementation/evidence commit, exact files changed, relationship-defect mapping, focused negative/mutation evidence, full regression results, scope/privacy review, limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit.
