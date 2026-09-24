# PL-0112 — Codex Work Order V01

Task: **PL-0112 — Glossy/PET capture preset**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0112_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the shared M04 quality/coverage engine and the accepted M03 capture/session architecture. Presets and modes configure authoritative shared policies; they must not fork new capture/sensor pipelines.

## Mandatory implementation

1. Define a versioned Glossy/PET preset emphasizing highlight clipping control, reflection guidance and denser orbit coverage.
2. Reuse PL-0096 clipping metrics and PL-0102 coverage model; do not create separate glossy-only analysis pipelines.
3. Persist effective thresholds/coverage requirements with the scan session.
4. Surface actionable guidance when highlight clipping repeatedly blocks acceptance.
5. Add tests comparing Glossy/PET against Matte/HDPE policy differences, persistence and threshold boundaries.

## Validation

Add behavior-bearing tests for preset/mode policy, persistence, warnings/blockers and exact boundaries. Run all relevant regression/project/static checks, `git diff --check`, protected-file and privacy/signing checks. Do not claim physical packaging/iPhone validation unless actually executed.

Create a distinct implementation commit and separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
