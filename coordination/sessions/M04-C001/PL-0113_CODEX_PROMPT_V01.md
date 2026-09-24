# PL-0113 — Codex Work Order V01

Task: **PL-0113 — Transparent packaging warning mode**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0113_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the shared M04 quality/coverage engine and the accepted M03 capture/session architecture. Presets and modes configure authoritative shared policies; they must not fork new capture/sensor pipelines.

## Mandatory implementation

1. Implement a transparent-packaging mode that clearly warns photogrammetry may fail without temporary matte treatment, textured inserts or background preparation.
2. Do not claim transparent reconstruction reliability that the current pipeline has not demonstrated.
3. Reuse the same capture/quality pipeline while allowing transparent-specific instructions and suitability warnings.
4. Record whether the user acknowledged preparation guidance and which temporary treatment mode was selected, without implying it was physically verified.
5. Add tests for preflight warning, acknowledgement state, treatment selection and no-false-suitability claims.

## Validation

Add behavior-bearing tests for preset/mode policy, persistence, warnings/blockers and exact boundaries. Run all relevant regression/project/static checks, `git diff --check`, protected-file and privacy/signing checks. Do not claim physical packaging/iPhone validation unless actually executed.

Create a distinct implementation commit and separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
