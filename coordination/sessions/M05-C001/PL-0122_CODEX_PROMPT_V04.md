# PL-0122 — Codex Remediation Work Order V04

Task: **PL-0122 — Pairing lifecycle already-idle and wrong-version closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0122_CODEX_LOG_V04.md

TASKS.md must authorize `M05-BATCH-004 / READY / CODEX`. Preserve all 10 accepted M05 children, accepted M03/M04, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Preserve the accepted architecture. Close only the final independent-audit gap.

## Mandatory remediation

1. Preserve functional manual pairing, persisted reconnect identity, QR scanner gating and ProductionCaptureCameraLifecycle stop/restore registration.
2. Represent the real production camera lifecycle with enough state to distinguish: active-and-stoppable, active-but-stop-failed, and already-released/idle.
3. QR acquisition must succeed when the production camera is already safely released; it must fail only when an active camera cannot be released.
4. Restore production capture only when pairing actually displaced an active production camera; do not spuriously restart an already-idle camera.
5. Add Swift tests for wrong-version PairingOffer rejection, active stop success, active stop refusal, already-idle success, no concurrent scanner/capture ownership and correct conditional hand-back.

Run production-seam behavior tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V04 log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
