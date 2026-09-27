# PL-0160 — ChatGPT Audit Criteria V01

Task: **COLMAP capability probe and version parser**

Parent:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Criteria:

1. Root TASKS.md authorizes M07-C001.
2. Parent master criteria remain mandatory.
3. Implement a deterministic COLMAP capability probe and version parser behind PackLab-owned code. It must distinguish configured/missing/unexecutable/unsupported/valid states without mutating the project or downloading software.
4. Use accepted PackLab project/job/process/provenance authorities; do not create a competing authority.
5. RAW_CAPTURE remains immutable.
6. No PL-0166+ implementation and no neural/generative model installation.
7. Add deterministic focused tests for the production seam introduced by this task.
8. Focused tests and exact full locked suite exit 0.
9. Relevant Ruff/mypy/compileall/diff/project checks pass truthfully.
10. Publish a separate child log at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0160_CODEX_LOG_V01.md using full GitHub URLs.
11. The child log ends exactly READY_FOR_INDEPENDENT_AUDIT.
