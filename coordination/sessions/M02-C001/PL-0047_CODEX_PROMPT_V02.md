# PL-0047 — Codex Remediation Work Order V02

Task: **PL-0047 — Intrinsics distortion model remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_LOG_V02.md

## Authorization

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0051 or M03 during this remediation batch.

## Authorized files

- `schemas/packscan/camera-intrinsics.schema.json`
- `docs/packscan/camera-intrinsics.md`
- `tests/fixtures/packscan/**`
- `tests/packscan/test_intrinsics_contract.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Make distortion branches explicit and machine-enforced by model.
2. For model none, require empty coefficient_order and empty coefficients.
3. For fisheye, require exact OpenCV order [k1,k2,k3,k4] and exactly four coefficients.
4. For Brown-Conrady, freeze one explicitly named supported coefficient order/version and require matching coefficient count; do not accept arbitrary strings or lengths.
5. Require coefficients whenever a non-none model is selected.
6. Preserve the existing matrix/origin/dimension-policy/provenance rules.
7. Add negative fixtures/tests for wrong order, missing coefficients, mismatched lengths and illegal coefficients for model none.

## Validation

Re-run all still-valid original task requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing: where the blocking audit identified an ambiguity, add a negative/mutation case that would fail on the pre-remediation contract.

No native/device/physical evidence may be fabricated.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files, defect mapping, validation commands/results, failures/fixes, regressions, scope/privacy, platform limitations and push/remote evidence.

End exactly with `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
