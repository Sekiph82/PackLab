# PL-0062 — Codex Remediation Work Order V02

Task: **PL-0062 — Marker policy source-of-truth integration remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-RESUME-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0067/PL-0068 or M03 during this remediation batch.

## Authorized files

- `core/src/packlab_core/calibration/**`
- `tests/calibration/test_marker_detection.py`
- `schemas/packscan/calibration-marker-policy.json`
- `docs/calibration/marker-detection.md`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Make the PL-0059 machine-readable marker policy the canonical source used by the detector for dictionary/family selection, directly or through one generated/shared PackLab policy loader.
2. Eliminate an independently hard-coded detector dictionary truth that can drift from calibration-marker-policy.json.
3. Fail clearly if the policy dictionary cannot be mapped to an available OpenCV aruco dictionary rather than silently substituting another family.
4. Add a regression that mutates or substitutes policy dictionary data and proves detector resolution follows/rejects the policy rather than an embedded constant.
5. Strengthen duplicate-marker-ID testing through injected/helper-level detector results so duplicate IDs deterministically produce the bounded duplicate_marker_id invalid outcome.
6. Preserve deterministic corner ordering/refinement, malformed-image handling and detection-only scope with no physical scale inference.

## Validation

Re-run all still-valid original V01 requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing against the exact pre-remediation defect. Do not substitute string-presence tests for semantic/geometry/binary/relationship behavior when the audit requires stronger proof.

Do not fabricate native Swift/Xcode/device/physical evidence.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_LOG_V02.md with synchronized start, implementation/evidence commit, exact files, defect mapping, focused negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
