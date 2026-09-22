# PL-0061 — Codex Remediation Work Order V02

Task: **PL-0061 — Printed-mat tolerance policy alignment remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-RESUME-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0067/PL-0068 or M03 during this remediation batch.

## Authorized files

- `docs/calibration/pre-use-verification.md`
- `docs/calibration/verification-record-template.md`
- `tests/calibration/test_pre_use_verification.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Choose one explicit A3 page-dimension tolerance policy and make procedure and reusable record template identical for width and height.
2. Preserve the existing A4 tolerance unless a documented reason requires a change.
3. Ensure marker/reference-distance tolerance and reprint/fail rules remain mutually consistent across procedure and template.
4. Add a regression that parses/extracts the authoritative tolerance values from both artifacts and compares them semantically rather than only checking text presence.
5. Add a mutation/helper case proving procedure/template drift is detected.
6. Preserve blank/UNRECORDED owner-physical-evidence fields and do not fabricate measurements.

## Validation

Re-run all still-valid original V01 requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing against the exact pre-remediation defect. Do not substitute string-presence tests for semantic/geometry/binary/relationship behavior when the audit requires stronger proof.

Do not fabricate native Swift/Xcode/device/physical evidence.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_LOG_V02.md with synchronized start, implementation/evidence commit, exact files, defect mapping, focused negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
