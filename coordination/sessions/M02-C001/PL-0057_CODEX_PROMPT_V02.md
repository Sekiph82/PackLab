# PL-0057 — Codex Remediation Work Order V02

Task: **PL-0057 — Swift deterministic ZIP writer remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-RESUME-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0067/PL-0068 or M03 during this remediation batch.

## Authorized files

- `apps/ios-capture/PackLabCapture/PackScan/**`
- `apps/ios-capture/PackLabCaptureTests/**`
- `tests/packscan/**`
- `tests/fixtures/packscan/**`
- `docs/packscan/swift-writer.md`
- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Encode the exact frozen DOS timestamp for 1980-01-01 00:00:00 in both local and central ZIP headers; do not write an all-zero DOS date.
2. Make the Swift writer's DEFLATE implementation honor the accepted PackScan level-9 contract deterministically. Use an API/implementation that explicitly sets level 9; do not merely label an uncontrolled compression call as level 9.
3. Ensure the raw ZIP payload uses method 8 DEFLATE framing appropriate to ZIP rather than a zlib/gzip wrapper.
4. Preserve deterministic entry order, no timestamp extra fields, CRC32, UTF-8 path bytes, path safety and partial-file safe finalization.
5. Add byte-level regression evidence that parses the emitted local/central header fields and verifies DOS date/time, method, flags, CRC/size and absence of extra timestamp fields.
6. If native Swift execution is unavailable on Windows, do not fabricate it. Add source/fixture evidence that is independently tied to the actual encoder implementation and leave native execution as a later macOS evidence boundary.
7. Do not add personal signing/team/provisioning settings.

## Validation

Re-run all still-valid original V01 requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing against the exact pre-remediation defect. Do not substitute string-presence tests for semantic/geometry/binary/relationship behavior when the audit requires stronger proof.

Do not fabricate native Swift/Xcode/device/physical evidence.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_LOG_V02.md with synchronized start, implementation/evidence commit, exact files, defect mapping, focused negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
