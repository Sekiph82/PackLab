# PL-0088 — Codex Remediation Work Order V04

Task: **PL-0088 — Crash transaction recovery closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0088_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. PL-0070 remains accepted; PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve all correct Batch-003 functionality and close the remaining persistence/destructive boundary only.

## Mandatory remediation
1. Redesign accepted-capture transaction recovery so source, canonical record and state move as one recoverable transaction across every crash point.
2. On reopen, either complete all three final publications from staged data or roll back all partial final/staged artifacts; never leave source/record committed with old state.
3. Handle crashes after source final move, after record final move, before/after state replacement, and malformed/missing transaction markers deterministically.
4. Add filesystem failure-injection tests for every transaction stage and prove reopen yields either the fully accepted capture or a clean pre-capture state.

Use real temporary-directory failure injection for filesystem boundaries. Run all available regression/static/project validation and git diff --check truthfully.

Create one implementation commit and one separate log-only commit. End the log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
