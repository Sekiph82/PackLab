# PL-0164 — Codex Work Order V01

Task: **Stage stdout/stderr and machine-readable results**

Repository:
https://github.com/Sekiph82/PackLab

Parent master:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0164_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Scope

Implement bounded per-stage process evidence and machine-readable stage results compatible with the accepted JobManager/subprocess authority. Preserve exit code, timing, cancellation/failure state and bounded logs without secrets/private absolute paths in portable provenance.

Preserve all accepted M06 authorities and stay inside the M07-C001 master safety/validation/commit rules.

Required child log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0164_CODEX_LOG_V01.md

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
