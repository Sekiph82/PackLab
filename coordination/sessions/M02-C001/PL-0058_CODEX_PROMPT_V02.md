# PL-0058 — Codex Remediation Work Order V02

Task: **PL-0058 — Real Swift-to-Python contract evidence remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-RESUME-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0067/PL-0068 or M03 during this remediation batch.

## Authorized files

- `tests/packscan/**`
- `tests/fixtures/packscan/**`
- `apps/ios-capture/PackLabCapture/PackScan/**`
- `docs/packscan/swift-writer.md`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Build the PL-0058 proof on the corrected PL-0057 writer; do not use the Python writer to manufacture the positive 'Swift output' package under test.
2. Provide deterministic Swift-side package bytes or an independently derived byte-level Swift encoder fixture whose provenance is explicitly tied to the corrected Swift implementation.
3. If no authorized macOS/Xcode execution exists, label the evidence honestly as source-derived/static and do not call it native Swift-produced execution evidence.
4. Make Python read/validate those Swift-side bytes through the real PackScan validator.
5. Verify schema/layout/checksum/photo metadata compatibility, not just hard-coded source strings.
6. Add a negative mutation to the Swift-side package bytes that leaves the rest of the package intact and prove Python rejects it.
7. Record fixture provenance: Swift source commit, contract/schema version, generation method and native-vs-static evidence level.

## Validation

Re-run all still-valid original V01 requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing against the exact pre-remediation defect. Do not substitute string-presence tests for semantic/geometry/binary/relationship behavior when the audit requires stronger proof.

Do not fabricate native Swift/Xcode/device/physical evidence.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CODEX_LOG_V02.md with synchronized start, implementation/evidence commit, exact files, defect mapping, focused negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
