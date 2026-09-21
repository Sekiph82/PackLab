# PL-0062 — Codex Work Order V01

Task: **PL-0062 — OpenCV marker detection and corner refinement**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_LOG_V01.md

## Scope

Read TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md, relevant accepted M00/M01 architecture/contracts, this prompt and its criteria. TASKS.md must authorize `M02-BATCH-001` / CODEX.

Authorized primary areas:
- `core/src/packlab_core/calibration/**`
- `tests/calibration/**`
- `docs/calibration/**`

Minimal adjacent files are allowed only when technically required and must be justified in the child log. Never edit TASKS.md, ChatGPT audit artifacts, or start M03.

## Requirements

1. Implement marker detection for the selected dictionary using OpenCV behind a PackLab-owned calibration API.
2. Implement deterministic corner refinement and return marker IDs, ordered pixel corners and quality/provenance metadata.
3. Reject/flag duplicates, malformed images and unsupported image shapes without crashing unrelated workflows.
4. Do not infer physical scale in this detection-only task.
5. Use synthetic/generated safe test images where possible and pin behavior to the selected dictionary constants.

## Validation and handoff

Run focused positive/negative/boundary tests, relevant regression tests, Ruff/mypy where Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Do not fabricate unavailable native/device/physical evidence. For PL-0068, real physical evidence is mandatory for completion.

Commit/push the child implementation/evidence, then publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_LOG_V01.md with start commit, implementation commit, files changed, commands/results, failures/fixes, limitations, scope/privacy review and push evidence. End `READY_FOR_INDEPENDENT_AUDIT`.
