# PL-0118 — Codex Work Order V01

Task: **PL-0118 — Scan-suitability preflight**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0118_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M04-BATCH-001` / `READY` / `CODEX`. M03 remains accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M05.

Reuse the shared M04 quality/coverage engine and the accepted M03 capture/session architecture. Presets and modes configure authoritative shared policies; they must not fork new capture/sensor pipelines.

## Mandatory implementation

1. Implement one deterministic preflight that evaluates selected preset, device/session readiness, storage/thermal/battery admission, calibration availability, preparation acknowledgements and minimum environment guidance before capture starts.
2. Differentiate hard blockers, warnings and informational guidance with stable reason codes.
3. PL-0068 calibration remains OWNER_REQUIRED; absence of owner-verified physical calibration must be represented truthfully and must follow the approved policy rather than fabricated acceptance.
4. Preflight must feed the real New Scan/start-capture workflow and persist its result/acknowledgements with the session.
5. Add table-driven tests for all presets, blockers/warnings, unavailable calibration, health conditions and exact start-eligibility behavior.

## Validation

Add behavior-bearing tests for preset/mode policy, persistence, warnings/blockers and exact boundaries. Run all relevant regression/project/static checks, `git diff --check`, protected-file and privacy/signing checks. Do not claim physical packaging/iPhone validation unless actually executed.

Create a distinct implementation commit and separate log-only commit. User-facing repository links must be full GitHub URLs.

End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
