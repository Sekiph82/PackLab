# PL-0041 — Codex Remediation Work Order V02

Task: **PL-0041 — iOS diagnostics privacy-default remediation**

Repository: https://github.com/Sekiph82/PackLab
Original/updated audit finding: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CHATGPT_AUDIT_V01.md
This remediation prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CODEX_PROMPT_V02.md
Frozen remediation criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CHATGPT_AUDIT_CRITERIA_V02.md
Required remediation log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CODEX_LOG_V02.md

## Authority

Root TASKS.md must authorize the M01 remediation batch and Required Actor CODEX. Read AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, coordination/AUDIT_POLICY.md, the relevant V01 prompt/criteria/log/audit history, and current files before work.

Before material work run:
- git fetch origin main --prune
- git rev-list --left-right --count HEAD...origin/main
- git status --porcelain

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md.

## Authorized files

- `apps/ios-capture/PackLabCapture/Diagnostics/DiagnosticsLogger.swift`
- `apps/ios-capture/PackLabCapture/Diagnostics/DiagnosticsExporter.swift`
- `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift`
- `docs/development/IOS_DIAGNOSTICS.md`

Minimal adjacent files are allowed only when technically necessary for the remediation and must be justified in the log.

## Mandatory remediation requirements

1. Add implementation-level sanitization/redaction before diagnostic strings are retained or exported.
2. Redact common token/secret/credential patterns and private user/home paths while keeping deterministic troubleshooting value.
3. Constrain or sanitize capability/environment strings before export.
4. Keep images/capture payloads, device identifiers, credentials and network upload outside the diagnostics model.
5. Preserve bounded retention, explicit user-initiated local export and no silent network transfer.
6. Add hardware-independent XCTest coverage for redaction, safe capability export, bounded retention and empty-export behavior; if native XCTest cannot run on Windows, still add source tests and static evidence without claiming execution.

## Full regression

Re-run the original task's still-valid mandatory criteria, not only the named defect. Preserve all accepted behavior from sibling M01 tasks. Run task-relevant focused tests/checks, git diff --check, git diff -- TASKS.md, exact changed-file review, protected-file review and privacy/secrets review.

For Swift/Xcode tasks, static project/source evidence on Windows is allowed but native Xcode/simulator/device success must not be fabricated.

## Handoff

Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files changed, defect-to-fix mapping, validation expected/failure/actual results, regressions, privacy/scope review, platform limitations and push evidence.

End with `AWAITING_AUDIT`. Do not self-audit. Do not start M02.
