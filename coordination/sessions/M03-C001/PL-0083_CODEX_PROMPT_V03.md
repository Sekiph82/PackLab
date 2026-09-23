# PL-0083 — Codex Remediation Work Order V03

Task: **PL-0083 — Live tracking recovery-policy remediation**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0083_CODEX_LOG_V03.md

TASKS.md must authorize M03-BATCH-003 / READY / CODEX. PL-0070 remains accepted and PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Preserve every previously passing behavior and close every finding in the previous independent audit.

## Mandatory remediation
1. Use TrackingRecoveryPolicy and TrackingWarningViewModel in the actual CaptureRuntimeViewModel flow instead of leaving them disconnected.
2. Feed live AR tracking updates continuously into the recovery/hysteresis policy, not only one startup snapshot.
3. Drive pose-evidence eligibility and visible warning clearing from the stabilized recovery state.
4. Retain degradation diagnostics and add tests for live flapping, sustained recovery, warning visibility and eligibility transitions.

Run focused behavior tests plus relevant M03 regression, project checks, git diff --check, protected-file and privacy/signing review. Native Xcode/iPhone results may be claimed only if actually executed.

Create a distinct implementation commit and a separate log-only commit. End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
