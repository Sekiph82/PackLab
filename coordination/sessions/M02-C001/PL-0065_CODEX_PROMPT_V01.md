# PL-0065 — Codex Work Order V01

Task: **PL-0065 — iPhone main-camera calibration procedure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CODEX_LOG_V01.md

## Scope

Read TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md, relevant accepted M00/M01 architecture/contracts, this prompt and its criteria. TASKS.md must authorize `M02-BATCH-001` / CODEX.

Authorized primary areas:
- `docs/calibration/**`
- `schemas/packscan/**`
- `tests/calibration/**`

Minimal adjacent files are allowed only when technically required and must be justified in the child log. Never edit TASKS.md, ChatGPT audit artifacts, or start M03.

## Requirements

1. Define when PackLab may rely on recorded EXIF/intrinsics versus when a dedicated iPhone main-camera calibration is required.
2. Document a repeatable calibration capture procedure, required views, focus/zoom/lens constraints and validation outputs.
3. Keep the baseline explicitly iPhone 16 Standard main camera and avoid LiDAR/Pro-only assumptions.
4. Define provenance/versioning fields needed to bind a calibration result to device/lens/resolution.
5. Do not fabricate owner-device measurements or claim a calibrated profile exists until physically produced.

## Validation and handoff

Run focused positive/negative/boundary tests, relevant regression tests, Ruff/mypy where Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Do not fabricate unavailable native/device/physical evidence. For PL-0068, real physical evidence is mandatory for completion.

Commit/push the child implementation/evidence, then publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0065_CODEX_LOG_V01.md with start commit, implementation commit, files changed, commands/results, failures/fixes, limitations, scope/privacy review and push evidence. End `READY_FOR_INDEPENDENT_AUDIT`.
