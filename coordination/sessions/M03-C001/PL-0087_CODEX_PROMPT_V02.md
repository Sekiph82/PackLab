# PL-0087 — Codex Remediation Work Order V02

Task: **PL-0087 — New Scan workflow remediation**

Repository: https://github.com/Sekiph82/PackLab
Master remediation batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0087_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M03-BATCH-002` / READY / CODEX and point to the master remediation prompt. PL-0070 must remain accepted; PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Read the previous implementation, prior prompt/criteria, and the independent audit. Preserve every accepted behavior and remediate every finding.

## Mandatory remediation

1. Make New Scan reachable from the actual PackLab Capture navigation/root workflow.
2. Provide visible validation state for invalid Start actions instead of silently swallowing validation failures.
3. Preserve the accepted M02 freehand/guided_orbit/turntable IDs and keep M04 guidance parameters out of this task.
4. Add behavior-bearing tests for cancellation, successful Start callback, invalid Start prevention and all capture-mode mappings.

## Validation

Add behavior-bearing positive, negative and boundary tests for every repaired path. Run all relevant deterministic tests/project checks available, `git diff --check`, protected-file/TASKS checks, exact scope review and privacy/signing review. Xcode/iPhone results may be claimed only if genuinely executed.

Create a distinct remediation implementation commit, then publish the matching log in a log-only commit. The log must map every prior failed criterion to the fix/evidence and end exactly:

`READY_FOR_INDEPENDENT_AUDIT`
