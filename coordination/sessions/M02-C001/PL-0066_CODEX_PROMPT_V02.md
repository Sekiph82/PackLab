# PL-0066 — Codex Remediation Work Order V02

Task: **PL-0066 — Fail-closed calibration-profile compatibility remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-RESUME-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0067/PL-0068 or M03 during this remediation batch.

## Authorized files

- `core/src/packlab_core/calibration/profile.py`
- `tests/calibration/test_profile_storage.py`
- `schemas/packscan/calibration-profile.schema.json`
- `docs/calibration/profile-storage.md`
- `core/src/packlab_core/calibration/__init__.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Make the persisted calibration-profile schema the canonical structural validation source before compatibility/reuse decisions, or use one equivalent generated validator without weaker duplicate rules.
2. A reusable measured/candidate profile must satisfy the required owner/native-capture/physical-measurement provenance states; unavailable provenance must fail closed.
3. Parse/validate timestamps as real RFC3339/UTC date-times rather than suffix-only checks.
4. Enforce positive resolution dimensions, required non-empty key fields, known resolution policy/schema version and all persisted confidence/RMSE/view-count ranges before reuse.
5. Preserve exact-match and explicitly allowed same-aspect resolution compatibility behavior only after structural/provenance validation succeeds.
6. Add tests for unavailable provenance, malformed timestamp, invalid dimensions, empty key fields, bad confidence score, bad RMSE, invalid accepted-view count and unknown policy/version.
7. Ensure every invalid structural/provenance case returns an explicit non-reusable reason and cannot silently fall through to compatible.

## Validation

Re-run all still-valid original V01 requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing against the exact pre-remediation defect. Do not substitute string-presence tests for semantic/geometry/binary/relationship behavior when the audit requires stronger proof.

Do not fabricate native Swift/Xcode/device/physical evidence.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_LOG_V02.md with synchronized start, implementation/evidence commit, exact files, defect mapping, focused negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
