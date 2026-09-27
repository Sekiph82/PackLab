# M07-C001 — Codex Master Work Order V01

Tasks: **PL-0158 through PL-0165**  
Repository: https://github.com/Sekiph82/PackLab  
Branch: `main`

Canonical tracker:
https://github.com/Sekiph82/PackLab/blob/main/TASKS.md

This prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_PROMPT_V01.md

Master audit criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CHATGPT_AUDIT_CRITERIA_V01.md

Mandatory architecture:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

Architecture decision:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/adr/ADR-0003-object-centric-reconstruction-authority.md

Dependency/license register:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/DEPENDENCY_LICENSE_REGISTER.md

Required master log:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_LOG_V01.md

## Authorization and safety

Read TASKS.md first. It must authorize M07-C001 / READY / CODEX for PL-0158 through PL-0165.

Fetch origin/main, require a clean/safely reconcilable worktree, and never reset, rebase, force-push, destructively clean or discard owner work.

Do not edit TASKS.md or any ChatGPT audit/criteria artifact.

## Architecture intent

This batch establishes the reconstruction foundation after the OpenReality architecture review.

PackLab V1 remains:
`PackScan -> COLMAP/OpenMVS -> reconstruction observation -> later M08 object isolation -> M09 metric scale -> M10 Scan Master`.

This batch must create the backend-neutral seam needed for future alternatives, but it must **not** install or integrate VGGT, SAM 3D Objects, TRELLIS or OpenReality itself.

OpenReality is a reference architecture, not a runtime vendor dependency.

## Child execution

Execute every child in order. Before each child, read its full prompt and criteria:

- PL-0158: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0158_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0158_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0159: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0159_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0159_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0160: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0160_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0160_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0161: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0161_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0161_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0162: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0162_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0162_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0163: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0163_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0163_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0164: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0164_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0164_CHATGPT_AUDIT_CRITERIA_V01.md
- PL-0165: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0165_CODEX_PROMPT_V01.md
  Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/PL-0165_CHATGPT_AUDIT_CRITERIA_V01.md

For every child:
1. inspect accepted production seams;
2. implement only the frozen child scope;
3. add production-boundary tests;
4. run focused validation and exact full locked suite;
5. run required static/project checks;
6. commit implementation/evidence;
7. create a separate child log-only commit;
8. push and verify remote visibility before the next child.

## Stop conditions

Stop rather than improvising if:
- a task requires PL-0166+ implementation;
- a selected binary/source cannot be identified reproducibly;
- a license/source fact cannot be verified;
- OpenMVS packaging/distribution would require a legal conclusion beyond the register;
- an engine installation requires destructive machine changes not authorized by the task;
- a model download/neural backend would be needed;
- accepted M06 authorities would have to be bypassed.

## Final handoff

Publish https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M07-C001/MASTER_CODEX_LOG_V01.md with full GitHub URLs, child commit/log index, full-suite/static results, dependency/license state and residual limitations.

End exactly:

`AWAITING_MILESTONE_AUDIT`

Stop. Do not start PL-0166.
