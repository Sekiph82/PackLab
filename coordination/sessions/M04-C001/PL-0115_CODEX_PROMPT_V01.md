# PL-0115 — Codex Work Order V01

Task: **PL-0115 — Closure/Cap macro-detail mode**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0115_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the shared M04 quality/coverage engine and the accepted M03 capture/session architecture. Presets and modes configure authoritative shared policies; they must not fork new capture/sensor pipelines.

## Mandatory implementation

1. Define a closure/cap detail mode with tighter framing, dedicated detail coverage and quality thresholds appropriate to caps, pumps and threads visible at phone-camera distances.
2. Keep capture on the supported iPhone main-camera architecture unless an explicitly supported lens choice is later authorized; do not silently switch lenses.
3. Integrate with the same quality, duplicate, metadata and session persistence paths.
4. Expose working-distance/framing guidance without claiming unsupported optical macro capability.
5. Add tests for mode policy, lens invariants, detail coverage and accepted/rejected framing.

## Validation

Add behavior-bearing tests for preset/mode policy, persistence, warnings/blockers and exact boundaries. Run all relevant regression/project/static checks, `git diff --check`, protected-file and privacy/signing checks. Do not claim physical packaging/iPhone validation unless actually executed.

Create a distinct implementation commit and separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
