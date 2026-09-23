# PL-0081 — Codex Remediation Work Order V02

Task: **PL-0081 — CoreMotion service/alignment remediation**

Repository: https://github.com/Sekiph82/PackLab
Master remediation batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0081_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M03-BATCH-002` / READY / CODEX and point to the master remediation prompt. PL-0070 must remain accepted; PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Read the previous implementation, prior prompt/criteria, and the independent audit. Preserve every accepted behavior and remediate every finding.

## Mandatory remediation

1. Put the CoreMotion implementation behind the existing MotionService seam and preserve simulator no-evidence behavior under the same contract.
2. Represent unavailable/start/update failures explicitly instead of silently returning or ignoring errors.
3. Bind the nearest eligible motion sample and alignment delta/status to each accepted capture timestamp.
4. Document the timestamp basis, preserve bounded buffering, and add tests for accepted-capture alignment, stale/missing data and provider failure.

## Validation

Add behavior-bearing positive, negative and boundary tests for every repaired path. Run all relevant deterministic tests/project checks available, `git diff --check`, protected-file/TASKS checks, exact scope review and privacy/signing review. Xcode/iPhone results may be claimed only if genuinely executed.

Create a distinct remediation implementation commit, then publish the matching log in a log-only commit. The log must map every prior failed criterion to the fix/evidence and end exactly:

`READY_FOR_INDEPENDENT_AUDIT`
