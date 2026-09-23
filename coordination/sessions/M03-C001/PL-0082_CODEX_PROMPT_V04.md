# PL-0082 — Codex Remediation Work Order V04

Task: **PL-0082 — Pose schema cross-check closure**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V03.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_V03.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_PROMPT_V04.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CHATGPT_AUDIT_CRITERIA_V04.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0082_CODEX_LOG_V04.md

TASKS.md must authorize M03-BATCH-004 / READY / CODEX. Preserve PL-0070 acceptance and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/audits. Never start M04.

Preserve current working Batch-003 implementation and close only the remaining frozen evidence/integration boundary.

## Mandatory remediation
1. Keep the existing numeric X/Y/Z rotation goldens, inverse/round-trip behavior and basis constant.
2. Add an authoritative contract fixture or mechanically generated test input sourced from schemas/packscan/pose.schema.json and assert coordinate convention, basis_conversion and metre unit constants against it.
3. Fail the test if the schema contract drifts from Swift constants rather than comparing only duplicated literals.
4. Preserve fail-closed invalid matrix behavior.

Where Apple frameworks cannot run on Windows, add injectable production-used seams and conditional XCTest sources; report native execution honestly.

Create one implementation commit and one log-only commit ending:

`READY_FOR_INDEPENDENT_AUDIT`
