# PL-0046 — Codex Remediation Work Order V02

Task: **PL-0046 — Per-photo field unit/range remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_LOG_V02.md

## Authorization

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0051 or M03 during this remediation batch.

## Authorized files

- `schemas/packscan/photo-metadata.schema.json`
- `docs/packscan/photo-metadata.md`
- `tests/fixtures/packscan/**`
- `tests/packscan/test_photo_metadata_contract.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Replace the generic unconstrained measurement contract with field-specific constraints for focal length, exposure, ISO and white balance.
2. Require focal length unit mm and a positive finite value when present.
3. Require exposure unit s and a positive finite value when present.
4. Require the frozen ISO unit token and an integer valid positive range when present.
5. Require white-balance unit K and a physically valid positive range when present.
6. Do not rely on nonstandard JSON-Schema keywords such as finite for portability.
7. Preserve explicit available/estimated/unavailable/not_recorded states and prohibit values for unavailable/not_recorded states.
8. Add negative fixtures/tests for wrong units, zero/negative values and fractional ISO.

## Validation

Re-run all still-valid original task requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing: where the blocking audit identified an ambiguity, add a negative/mutation case that would fail on the pre-remediation contract.

No native/device/physical evidence may be fabricated.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files, defect mapping, validation commands/results, failures/fixes, regressions, scope/privacy, platform limitations and push/remote evidence.

End exactly with `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
