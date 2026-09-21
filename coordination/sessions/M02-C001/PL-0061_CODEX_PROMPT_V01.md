# PL-0061 — Codex Work Order V01

Task: **PL-0061 — Printed-mat physical verification procedure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_LOG_V01.md

## Scope

Read TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md, relevant accepted M00/M01 architecture/contracts, this prompt and its criteria. TASKS.md must authorize `M02-BATCH-001` / CODEX.

Authorized primary areas:
- `docs/calibration/**`
- `tests/calibration/**`
- `assets/calibration/**`

Minimal adjacent files are allowed only when technically required and must be justified in the child log. Never edit TASKS.md, ChatGPT audit artifacts, or start M03.

## Requirements

1. Define a pre-use verification procedure using ruler/caliper measurements at multiple labelled reference distances.
2. Specify acceptance tolerances, measurement recording fields, printer scaling failure handling and reprint criteria.
3. Separate nominal document geometry from owner-measured physical geometry.
4. Provide a reusable verification record/template with no fabricated measurements.
5. Add a schema/validation check for verification records if machine-readable records are introduced.

## Validation and handoff

Run focused positive/negative/boundary tests, relevant regression tests, Ruff/mypy where Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Do not fabricate unavailable native/device/physical evidence. For PL-0068, real physical evidence is mandatory for completion.

Commit/push the child implementation/evidence, then publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_LOG_V01.md with start commit, implementation commit, files changed, commands/results, failures/fixes, limitations, scope/privacy review and push evidence. End `READY_FOR_INDEPENDENT_AUDIT`.
