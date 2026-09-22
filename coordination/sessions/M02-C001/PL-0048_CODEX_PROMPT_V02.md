# PL-0048 — Codex Remediation Work Order V02

Task: **PL-0048 — ARKit-to-PackScan pose basis remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_LOG_V02.md

## Authorization

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0051 or M03 during this remediation batch.

## Authorized files

- `schemas/packscan/pose.schema.json`
- `docs/packscan/pose.md`
- `tests/fixtures/packscan/**`
- `tests/packscan/test_pose_contract.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Freeze the exact ARKit camera/world to PackScan basis conversion, including source/destination axis directions, handedness, viewing direction and matrix multiplication/order convention.
2. Account explicitly for ARKit camera viewing along negative Z versus PackScan stored +Z-forward convention; a column-major/row-major memory-layout conversion alone is insufficient.
3. Freeze translation units explicitly as metres or another single named canonical unit.
4. Require coordinate_convention for stored available/degraded poses.
5. Constrain valid status/tracking_state combinations so contradictory combinations are rejected.
6. Define quaternion conversion consistently with the same basis change and preserve xyzw ordering.
7. Add deterministic synthetic basis-vector/pose tests and negative fixtures for contradictory tracking states.
8. Preserve no-LiDAR assumptions and do not claim native ARKit execution on Windows.

## Validation

Re-run all still-valid original task requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing: where the blocking audit identified an ambiguity, add a negative/mutation case that would fail on the pre-remediation contract.

No native/device/physical evidence may be fabricated.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files, defect mapping, validation commands/results, failures/fixes, regressions, scope/privacy, platform limitations and push/remote evidence.

End exactly with `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
