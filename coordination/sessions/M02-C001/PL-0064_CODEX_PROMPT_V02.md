# PL-0064 — Codex Remediation Work Order V02

Task: **PL-0064 — Calibration confidence threshold semantics remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_LOG_V02.md

## Authorization gate

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-RESUME-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0067/PL-0068 or M03 during this remediation batch.

## Authorized files

- `core/src/packlab_core/calibration/confidence.py`
- `tests/calibration/test_confidence.py`
- `docs/calibration/confidence-thresholds.md`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Choose and freeze one semantics for residual/spread thresholds: either true hard consistency gates or score-normalization reference values.
2. If they are hard maxima, fail closed above them. If they are scoring reference values, rename constants/docs so 'MAX'/'gate' language does not imply hard rejection.
3. Add immediate below/exact/above boundary tests for residual 0.05, edge spread 0.03, marker-count full-credit 4, accepted score 0.80 and warning score 0.60.
4. Add adversarial tests where one metric is beyond its frozen boundary while the other factors are strong, proving the chosen semantics.
5. Preserve deterministic accepted/warning/rejected outputs and the explicit provisional/non-physical-accuracy status.

## Validation

Re-run all still-valid original V01 requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing against the exact pre-remediation defect. Do not substitute string-presence tests for semantic/geometry/binary/relationship behavior when the audit requires stronger proof.

Do not fabricate native Swift/Xcode/device/physical evidence.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_LOG_V02.md with synchronized start, implementation/evidence commit, exact files, defect mapping, focused negative/mutation evidence, full regressions, scope/privacy review, platform limitations and remote visibility.

End exactly `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
