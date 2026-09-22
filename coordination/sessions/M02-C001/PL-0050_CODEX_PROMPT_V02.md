# PL-0050 — Codex Remediation Work Order V02

Task: **PL-0050 — Object-mask evidence/current-state closure**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CODEX_LOG_V02.md

## Authorization

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0051 or M03 during this remediation batch.

## Authorized files

- `coordination/sessions/M02-C001/PL-0050_CODEX_LOG_V02.md`
- `tests/packscan/test_object_mask_contract.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Do not edit or replace the historical V01 Codex log; preserve it as the record of the network stop.
2. Revalidate the existing PL-0050 implementation on current main and record the actual publication history truthfully in a new V02 log.
3. Add a lightweight repeatable contract regression proving omitted masks are valid and that the fixture-level dimension/linkage mismatch invariants are detected.
4. Keep cross-record dimension/linkage rejection explicitly assigned to the later runtime validator unless implementing that validator is independently justified within this child.
5. Do not rewrite the object-mask schema/docs merely to manufacture an implementation diff unless the revalidation finds a real defect.
6. End the V02 child log with READY_FOR_INDEPENDENT_AUDIT and accurately record current remote visibility.

## Validation

Re-run all still-valid original task requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing: where the blocking audit identified an ambiguity, add a negative/mutation case that would fail on the pre-remediation contract.

No native/device/physical evidence may be fabricated.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files, defect mapping, validation commands/results, failures/fixes, regressions, scope/privacy, platform limitations and push/remote evidence.

End exactly with `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
