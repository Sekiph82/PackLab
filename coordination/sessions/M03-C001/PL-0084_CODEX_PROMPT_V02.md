# PL-0084 — Codex Remediation Work Order V02

Task: **PL-0084 — AR reset/relocalization integration remediation**

Repository: https://github.com/Sekiph82/PackLab
Master remediation batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0084_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M03-BATCH-002` / READY / CODEX and point to the master remediation prompt. PL-0070 must remain accepted; PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Read the previous implementation, prior prompt/criteria, and the independent audit. Preserve every accepted behavior and remediate every finding.

## Mandatory remediation

1. Wire reset/relocalization through the single ARSession owner and use explicit ARSession run options only when required.
2. Connect user-requested, interruption and tracking-degradation reset triggers to the orchestration path.
3. Preserve immutable accepted captures while preventing pose continuity across localization epochs.
4. Persist reset reason/epoch diagnostics, expose relocalizing/recovered/failed state, and test idle/active/degraded/repeated resets.

## Validation

Add behavior-bearing positive, negative and boundary tests for every repaired path. Run all relevant deterministic tests/project checks available, `git diff --check`, protected-file/TASKS checks, exact scope review and privacy/signing review. Xcode/iPhone results may be claimed only if genuinely executed.

Create a distinct remediation implementation commit, then publish the matching log in a log-only commit. The log must map every prior failed criterion to the fix/evidence and end exactly:

`READY_FOR_INDEPENDENT_AUDIT`
