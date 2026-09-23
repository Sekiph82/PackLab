# PL-0076 — Codex Remediation Work Order V02

Task: **PL-0076 — PackScan per-photo metadata contract remediation**

Repository: https://github.com/Sekiph82/PackLab
Master remediation batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0076_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M03-BATCH-002` / READY / CODEX and point to the master remediation prompt. PL-0070 must remain accepted; PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Read the previous implementation, prior prompt/criteria, and the independent audit. Preserve every accepted behavior and remediate every finding.

## Mandatory remediation

1. Make the Swift wire model encode exactly to schemas/packscan/photo-metadata.schema.json, including source-status wire values, estimated status, ISO integer semantics, orientation object, snake_case keys and allowed properties.
2. Keep app-only lens/timestamp state outside the strict photo object or map it into the correct accepted PackScan contract location.
3. Implement atomic accepted-source + metadata persistence/binding rather than a validation-only helper.
4. Add cross-contract tests that serialize Swift metadata and validate against the authoritative M02 schema/fixtures, including unavailable/estimated and mismatch cases.

## Validation

Add behavior-bearing positive, negative and boundary tests for every repaired path. Run all relevant deterministic tests/project checks available, `git diff --check`, protected-file/TASKS checks, exact scope review and privacy/signing review. Xcode/iPhone results may be claimed only if genuinely executed.

Create a distinct remediation implementation commit, then publish the matching log in a log-only commit. The log must map every prior failed criterion to the fix/evidence and end exactly:

`READY_FOR_INDEPENDENT_AUDIT`
