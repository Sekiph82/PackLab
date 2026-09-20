# PL-0043 — Codex Child Work Order V01

Task: **PL-0043 — Add iOS unit-test target and initial smoke test**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V01.md

## Authority and synchronization

Read root TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, relevant M00 architecture/governance documents, and all artifacts produced by earlier M01 children that this task depends on.

TASKS.md must still authorize `M01-BATCH-001` / `CODEX`.

Before material work run and record:
`git fetch origin main --prune`
`git rev-list --left-right --count HEAD...origin/main`
`git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work.

## Authorized outputs

- `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift`

Additional minimal adjacent files are allowed only when technically necessary to make the authorized output valid, and every such file must be justified in the log.

## Mandatory requirements

1. Add a unit-test target to the Xcode project with at least one deterministic smoke test covering foundation code that does not require camera hardware.
2. Keep test target free of signing secrets and personal team settings.
3. Ensure the test can run on simulator/macOS CI once M16 provides the runner.
4. Document what was statically verified now versus what requires xcodebuild on macOS.
5. Do not claim physical-device or camera validation.

## Validation

Run all task-relevant focused tests/checks plus:
- `git diff --check`
- `git diff -- TASKS.md`
- exact changed-file review
- protected-file review
- privacy/secrets review
- relevant earlier-M01 regression checks.

For new files, use a diff/staged review that can actually see untracked content.

Platform-specific evidence must be truthful. Windows must not be represented as native Xcode/macOS. If a required validation is impossible without a future authorized platform, record the limitation and satisfy only the frozen criterion actually required here; never fabricate a pass.

## Boundaries

Do not edit TASKS.md. Do not self-audit. Do not create ChatGPT audit files. Do not start M02. Do not pull future PackScan/capture/reconstruction/CAD behavior into M01.

If this child cannot satisfy its frozen mandatory requirements safely, stop the entire M01 batch and publish the child/master stop evidence.

## Log and handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V01.md with start commit, implementation/evidence commit, full prompt/criteria URLs, files read/changed, exact validation evidence, failures/fixes, scope/privacy review, platform limitations and remote visibility.

End the child log with `READY_FOR_INDEPENDENT_AUDIT`. Do not predeclare the future log commit SHA.
