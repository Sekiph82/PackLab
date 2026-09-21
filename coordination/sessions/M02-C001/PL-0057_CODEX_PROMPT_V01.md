# PL-0057 — Codex Work Order V01

Task: **PL-0057 — Swift PackScan writer**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_LOG_V01.md

## Scope

Read TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md, relevant accepted M00/M01 architecture/contracts, this prompt and its criteria. TASKS.md must authorize `M02-BATCH-001` / CODEX.

Authorized primary areas:
- `apps/ios-capture/PackLabCapture/PackScan/**`
- `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`
- `tests/fixtures/packscan/**`
- `docs/packscan/**`

Minimal adjacent files are allowed only when technically required and must be justified in the child log. Never edit TASKS.md, ChatGPT audit artifacts, or start M03.

## Requirements

1. Implement a PackLab-owned Swift PackScan writer matching the frozen container/schema/checksum contract.
2. Keep platform/device APIs behind existing Capture service boundaries and do not make Swift types the cross-platform truth.
3. Write deterministic manifest/photo metadata/checksum structures compatible with Python expectations.
4. Use safe local temporary/finalization behavior so an interrupted write cannot masquerade as a complete package.
5. Do not add personal signing/team settings or fabricate native Xcode execution on Windows.
6. Provide deterministic source/static fixture evidence sufficient for later cross-language tests.

## Validation and handoff

Run focused positive/negative/boundary tests, relevant regression tests, Ruff/mypy where Python is touched, `git diff --check`, `git diff -- TASKS.md`, exact changed-file review and privacy/secrets review.

Do not fabricate unavailable native/device/physical evidence. For PL-0068, real physical evidence is mandatory for completion.

Commit/push the child implementation/evidence, then publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_LOG_V01.md with start commit, implementation commit, files changed, commands/results, failures/fixes, limitations, scope/privacy review and push evidence. End `READY_FOR_INDEPENDENT_AUDIT`.
