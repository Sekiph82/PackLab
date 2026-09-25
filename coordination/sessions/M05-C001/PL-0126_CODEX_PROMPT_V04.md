# PL-0126 — Codex Remediation Work Order V04

Task: **PL-0126 — Complete transfer UI/service failure and restore matrix**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0126_CODEX_LOG_V04.md

TASKS.md must authorize `M05-BATCH-004 / READY / CODEX`. Preserve all 10 accepted M05 children, accepted M03/M04, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Preserve the accepted architecture. Close only the final independent-audit gap.

## Mandatory remediation

1. Preserve the real finalized-history → FinalizedTransferWorkflowView → TransferScreen path and PL-0124 same-ID resume.
2. Extend FakeProductionTransferClient or equivalent production-client test seam to drive network cancel, authoritative status query, same-ID reconnect/resume, monotonic confirmed progress, checksum/digest retryable failure, terminal failure and verified completion.
3. Add a fresh TransferViewModel/runtime restore test proving visible phase, confirmed bytes and receiver identity are rebuilt from persisted sender identity plus receiver status, not optimistic local counters.
4. Cancel must retain finalized source and resumable identity; terminal failure must be visibly distinct from retryable failure; verified completion alone clears sender identity.
5. Keep all frozen UI phases reachable/truthful.

Run production-seam behavior tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V04 log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
