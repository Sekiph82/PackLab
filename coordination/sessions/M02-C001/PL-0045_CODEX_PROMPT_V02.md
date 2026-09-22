# PL-0045 — Codex Remediation Work Order V02

Task: **PL-0045 — SHA-256 representation contract remediation**

Repository: https://github.com/Sekiph82/PackLab
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CODEX_LOG_V02.md

## Authorization

Read TASKS.md, AGENTS.md, coordination/MILESTONE_BATCH_PROTOCOL.md, the original V01 prompt/criteria/log, the blocking audit above, this V02 prompt and its criteria.

TASKS.md must authorize `M02-REMEDIATION-BATCH-001` / CODEX. Otherwise stop `TASK_STATE_MISMATCH`.

Before material work:
- `git fetch origin main --prune`
- `git rev-list --left-right --count HEAD...origin/main`
- `git status --porcelain`

Require safe synchronized state. Never reset/rebase/force-push/destructively clean/stash owner work. Never edit TASKS.md. Never start PL-0051 or M03 during this remediation batch.

## Authorized files

- `schemas/packscan/manifest.schema.json`
- `docs/packscan/manifest-contract.md`
- `tests/fixtures/packscan/manifest-valid.json`
- `tests/fixtures/packscan/manifest-invalid-local-time.json`
- `tests/fixtures/packscan/manifest-invalid-unknown-property.json`
- `tests/packscan/test_manifest_contract.py`

Minimal adjacent files are allowed only when technically necessary and must be justified in the log.

## Mandatory remediation requirements

1. Correct the checksum canonicalization identifier so it describes SHA-256 as 32 digest bytes rendered as exactly 64 lowercase hexadecimal characters.
2. Use one unambiguous versioned identifier consistently in schema, docs and fixtures.
3. Preserve the existing 64 lowercase hex-character regex and strict timestamp/device/payload/privacy rules.
4. Add a focused regression proving the canonicalization identifier and digest length semantics cannot drift apart.
5. Do not weaken additionalProperties, path, source-authority or version constraints.

## Validation

Re-run all still-valid original task requirements plus the focused remediation checks. Run relevant pytest, Ruff/mypy when Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Tests must be sensitivity-bearing: where the blocking audit identified an ambiguity, add a negative/mutation case that would fail on the pre-remediation contract.

No native/device/physical evidence may be fabricated.

## Handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CODEX_LOG_V02.md. Record synchronized start, implementation/evidence commit, exact files, defect mapping, validation commands/results, failures/fixes, regressions, scope/privacy, platform limitations and push/remote evidence.

End exactly with `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit.
