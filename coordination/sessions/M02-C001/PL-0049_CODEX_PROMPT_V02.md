# PL-0049 — Codex Remediation Work Order V02

Task: **PL-0049 — CoreMotion clock/reference-frame remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_LOG_V02.md

## Authorization

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0051 or M03 during this remediation batch.

## Authorized files

- `schemas/packscan/motion.schema.json`
- `docs/packscan/motion.md`
- `tests/fixtures/packscan/**`
- `tests/packscan/test_motion_contract.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Preserve the native CoreMotion monotonic timestamp in seconds since device boot for each motion sample.
2. Define the photo/capture clock domain separately and record the mapping/anchor used to relate native monotonic motion time to UTC/photo time.
3. Record mapping uncertainty/resolution and synchronization tolerance so no precision finer than evidence is implied.
4. Record the selected CMAttitudeReferenceFrame as a frozen machine-readable value.
5. Constrain available samples to contain the required motion payload and unavailable samples not to carry valid motion vectors.
6. Keep stale and out_of_window states explicit and define how nearest/interpolated association uses the two-clock mapping.
7. Add aligned/stale/missing fixtures/tests that exercise the native clock mapping, reference frame and contradictory state rejection.
8. Preserve CoreMotion units and do not fabricate device execution.

## Validation

Re-run all still-valid original task requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing: where the blocking audit identified an ambiguity, add a negative/mutation case that would fail on the pre-remediation contract.

No native/device/physical evidence may be fabricated.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files, defect mapping, validation commands/results, failures/fixes, regressions, scope/privacy, platform limitations and push/remote evidence.

End exactly with `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
