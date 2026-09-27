# PL-0160 — Codex Work Order V01

Task: **COLMAP capability probe and version parser**

Repository:
https://github.com/Sekiph82/PackLab

Parent master:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md

Criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0160_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Scope

Implement a deterministic COLMAP capability probe and version parser behind PackLab-owned code. It must distinguish configured/missing/unexecutable/unsupported/valid states without mutating the project or downloading software.

Preserve all accepted M06 authorities and stay inside the M07-C001 master safety/validation/commit rules.

Required child log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0160_CODEX_LOG_V01.md

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
