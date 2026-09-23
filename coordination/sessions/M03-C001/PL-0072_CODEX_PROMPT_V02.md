# PL-0072 — Codex Remediation Work Order V02

Task: **PL-0072 — Original source + metadata preservation remediation**

Repository: https://github.com/Sekiph82/PackLab
Master remediation batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/MASTER_REMEDIATION_CODEX_PROMPT_V01.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_PROMPT_V02.md
Frozen criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CHATGPT_AUDIT_CRITERIA_V02.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M03-C001/PL-0072_CODEX_LOG_V02.md

## Authorization

TASKS.md must authorize `M03-BATCH-002` / READY / CODEX and point to the master remediation prompt. PL-0070 must remain accepted; PL-0068 must remain unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audits. Never start M04.

Read the previous implementation, prior prompt/criteria, and the independent audit. Preserve every accepted behavior and remediate every finding.

## Mandatory remediation

1. Persist exact original captured still bytes in an immutable master source path and verify digest/dimensions after write.
2. Extract available HEIF/JPEG EXIF/TIFF/ImageIO metadata from the original payload and preserve unknown metadata where technically safe.
3. Keep thumbnail/preview derivatives in physically separate paths that can never overwrite the master source.
4. Add tests for metadata extraction/preservation, immutable write protection, derivative separation, digest mismatch and dimension mismatch.

## Validation

Add behavior-bearing positive, negative and boundary tests for every repaired path. Run all relevant deterministic tests/project checks available, `git diff --check`, protected-file/TASKS checks, exact scope review and privacy/signing review. Xcode/iPhone results may be claimed only if genuinely executed.

Create a distinct remediation implementation commit, then publish the matching log in a log-only commit. The log must map every prior failed criterion to the fix/evidence and end exactly:

`READY_FOR_INDEPENDENT_AUDIT`
