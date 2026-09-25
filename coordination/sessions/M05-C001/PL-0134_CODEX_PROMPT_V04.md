# PL-0134 — Codex Remediation Work Order V04

Task: **PL-0134 — Persisted sender-state executable harness closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0134_CODEX_LOG_V04.md

TASKS.md must authorize `M05-BATCH-004 / READY / CODEX`. Preserve all 10 accepted M05 children, accepted M03/M04, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Preserve the accepted architecture. Close only the final independent-audit gap.

## Mandatory remediation

1. Preserve the real HTTPS receiver, shared V1 fixture, test TLS material, invalid-package quarantine matrix and exactly-once ingest assertions.
2. Make the executable harness genuinely simulate sender restart: write sender state, destroy the first sender object, create a fresh sender, read/validate persisted transfer ID + package digest + receiver identity, and derive all resumed requests from that restored state rather than hard-coded literals.
3. Verify the restored package digest and receiver identity before querying status; conflicting persisted state must fail closed.
4. Apply the same completion acceptance rules as production Swift: transfer ID match, package digest match, authenticated=true, verified=true and terminal verified/complete state.
5. Explicitly verify the live receiver certificate fingerprint equals the paired offer fingerprint before authenticated transfer operations.
6. Keep partial upload, receiver restart, cancel/resume, verified completion and exactly-once raw/index/report assertions in one coherent executable chain.

Run production-seam behavior tests, full locked suite, relevant Swift/project/static checks, Ruff/compileall, `git diff --check`, protected-file and privacy/secret checks. Native/physical claims only if genuinely executed.

Create one implementation/evidence commit and one separate V04 log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
