# PL-0163 — ChatGPT Audit Criteria V01

Task: **Normalized reconstruction backend contract**

Parent:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Mandatory implementation spec:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0163_RECONSTRUCTION_BACKEND_CONTRACT.md

Criteria:

1. Root TASKS.md authorizes M07-C001.
2. Parent master criteria remain mandatory.
3. Implement the PackLab-owned ReconstructionBackend domain contract exactly within the authority boundaries defined by the mandatory implementation spec. The V1 concrete composition is COLMAP/OpenMVS; future neural backends are only a seam in this task, not an implementation.
4. Use accepted PackLab project/job/process/provenance authorities; do not create a competing authority.
5. RAW_CAPTURE remains immutable.
6. No PL-0166+ implementation and no neural/generative model installation.
7. Add deterministic focused tests for the production seam introduced by this task.
8. Focused tests and exact full locked suite exit 0.
9. Relevant Ruff/mypy/compileall/diff/project checks pass truthfully.
10. Publish a separate child log at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0163_CODEX_LOG_V01.md using full GitHub URLs.
11. The child log ends exactly READY_FOR_INDEPENDENT_AUDIT.
