# PL-0043 — Codex Remediation Work Order V03

Task: **PL-0043 — Durable hosted-XCTest graph regression remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V03.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V03.md

## Gate

Read AGENTS.md, TASKS.md, the blocking audit above, this prompt and its criteria. TASKS.md must authorize M01-REMEDIATION-BATCH-002 / CODEX.

Before material work:
```
git fetch origin main --prune
git rev-list --left-right --count HEAD...origin/main
git status --porcelain
```

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Do not start M02.

## Authorized files

- `tests/tools/test_ios_project_graph.py`
- `docs/development/IOS_BASELINE.md`

Use only minimal adjacent files if technically unavoidable and justify them in the log.

## Mandatory requirements

1. Do not rewrite the now-correct Xcode project merely to manufacture a diff.
2. Add a durable, Xcode-free Python regression test that reads the source-controlled project.pbxproj.
3. Assert app testability is enabled for the test-used app configuration(s), PackLabCaptureTests has the expected BUNDLE_LOADER and TEST_HOST=$(BUNDLE_LOADER), test source membership exists, and the test target depends on PackLabCapture.
4. Assert personal DEVELOPMENT_TEAM, CODE_SIGN_IDENTITY and provisioning-profile settings remain absent.
5. The test must fail against the pre-remediation project graph and run in the normal pytest suite on Windows/Linux without Xcode.
6. Update IOS_BASELINE.md to identify the durable static regression test. Do not claim xcodebuild/simulator/device evidence.

## Validation

Re-run the still-valid original/V02 criteria, focused regression tests, full relevant M01 regression, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review, protected-file review and privacy/secrets review.

For unavailable native platform evidence, state the limitation rather than fabricating a pass.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V03.md with synchronized start, implementation/evidence commit, exact files, defect mapping, commands/results, failures/fixes, scope/privacy, limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit.
