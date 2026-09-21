# PL-0068 — Codex Work Order V01

Task: **PL-0068 — First physical calibration benchmark**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CODEX_LOG_V01.md

## Scope

Read TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md, relevant accepted M00/M01 architecture/contracts, this prompt and its criteria. TASKS.md must authorize `M02-BATCH-001` / CODEX.

Authorized primary areas:
- `docs/calibration/benchmarks/**`
- `tests/calibration/**`
- `assets/calibration/**`

Minimal adjacent files are allowed only when technically required and must be justified in the child log. Never edit TASKS.md, ChatGPT audit artifacts, or start M03.

## Requirements

1. Define and execute the first physical calibration benchmark using a printed verified PackLab mat and real measurements.
2. Record device/lens/resolution, printed-mat verification measurements, capture procedure, sample count, measured known dimensions, estimated dimensions and error statistics.
3. Use millimetres and report absolute plus percentage error without hiding rejected samples.
4. Do not fabricate physical measurements, owner-device execution or benchmark results.
5. If real owner-supplied physical evidence is unavailable, create only the benchmark template/procedure if needed, publish an OWNER_REQUIRED/BATCH_STOPPED log, and stop without claiming task completion.

## Validation and handoff

Run focused positive/negative/boundary tests, relevant regression tests, Ruff/mypy where Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Do not fabricate unavailable native/device/physical evidence. For PL-0068, real physical evidence is mandatory for completion.

Commit/push the child implementation/evidence, then publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0068_CODEX_LOG_V01.md with start commit, implementation commit, files changed, commands/results, failures/fixes, limitations, scope/privacy review and push evidence. End `READY_FOR_INDEPENDENT_AUDIT`.
