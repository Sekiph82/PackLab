# PL-0163 — Codex Work Order V01

Task: **Normalized reconstruction backend contract**

Repository:
https://github.com/Sekiph82/PackLab

Parent master:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0163_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Mandatory implementation spec:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

## Scope

Implement the PackLab-owned ReconstructionBackend domain contract exactly within the authority boundaries defined by the mandatory implementation spec. The V1 concrete composition is COLMAP/OpenMVS; future neural backends are only a seam in this task, not an implementation.

Preserve all accepted M06 authorities and stay inside the M07-C001 master safety/validation/commit rules.

Required child log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0163_CODEX_LOG_V01.md

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
