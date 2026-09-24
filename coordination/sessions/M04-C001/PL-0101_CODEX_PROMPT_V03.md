# PL-0101 — Codex Remediation Work Order V03

Task: **PL-0101 — Corrupt quality-log fail-closed closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0101_CODEX_LOG_V03.md

TASKS.md must authorize M04-BATCH-003 / READY / CODEX. Preserve all 16 accepted M04 children, accepted M03, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

The production M04 architecture is already integrated. Do not add parallel camera/AR/motion/quality/session ownership. Close only the remaining frozen evidence/state gap.

## Mandatory remediation

1. Preserve production every-candidate logging and bounded/sanitized JSONL behavior.
2. Add a real filesystem test that writes malformed/corrupt quality-candidates.jsonl and proves snapshot/reopen fails with QualityLogStoreError.corruptLog.
3. Prove corrupt quality diagnostics do not mutate or corrupt canonical accepted-capture/session files.
4. Preserve accepted/rejected ordering and bounded trim behavior.

## Validation

- Add behavior-bearing tests at the production-used seam.
- Run focused tests and the full declared locked suite.
- Run relevant project/static checks and `git diff --check`.
- Verify TASKS.md and ChatGPT audits are untouched.
- Review privacy/signing/secret/cache scope.
- Do not claim unavailable native iPhone/Xcode/physical calibration evidence.

Create one implementation commit and one separate log-only commit.

Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
