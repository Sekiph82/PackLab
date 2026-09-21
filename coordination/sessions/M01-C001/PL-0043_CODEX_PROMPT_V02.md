# PL-0043 — Codex Remediation Work Order V02

Task: **PL-0043 — Hosted XCTest target wiring remediation**

Repository: https://github.com/Sekiph82/PackLab
Original/updated audit finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V01.md
This remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V02.md
Frozen remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V02.md
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V02.md

## Authority

Root TASKS.md must authorize the M01 remediation batch and Required Actor CODEX. Read AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, the relevant V01 prompt/criteria/log/audit history, and current files before work.

Before material work run:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md.

## Authorized files

- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`
- `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift`
- `docs/development/IOS_BASELINE.md`

Minimal adjacent files are allowed only when technically necessary for the remediation and must be justified in the log.

## Mandatory remediation requirements

1. Make the hosted app unit-test target source-controlled graph coherent for future simulator/macOS CI.
2. If @testable import remains, enable app-target testability for the configuration used by tests; alternatively replace @testable with normal import only if every tested API is public and that is intentional.
3. Configure BUNDLE_LOADER and TEST_HOST coherently for hosted application unit tests.
4. Preserve app-target dependency, Swift 6 strict-concurrency settings, no personal DEVELOPMENT_TEAM/CODE_SIGN_IDENTITY/provisioning values, and hardware-independent tests.
5. Add static regression checks for testability, bundle loader, test host and source membership.
6. Do not claim xcodebuild test, simulator, signing or physical-device execution on Windows.

## Full regression

Re-run the original task's still-valid mandatory criteria, not only the named defect. Preserve all accepted behavior from sibling M01 tasks. Run task-relevant focused tests/checks, git diff --check, git diff -- TASKS.md, exact changed-file review, protected-file review and privacy/secrets review.

For Swift/Xcode tasks, static project/source evidence on Windows is allowed but native Xcode/simulator/device success must not be fabricated.

## Handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files changed, defect-to-fix mapping, validation expected/failure/actual results, regressions, privacy/scope review, platform limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit. Do not start M02.
