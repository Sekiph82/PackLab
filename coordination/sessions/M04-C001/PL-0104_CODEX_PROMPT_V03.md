# PL-0104 — Codex Remediation Work Order V03

Task: **PL-0104 — Auto-capture gate-matrix closure**

Repository: https://github.com/Sekiph82/PackLab
Master remediation: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/MASTER_REMEDIATION_CODEX_PROMPT_V02.md
Previous audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_V02.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_PROMPT_V03.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CHATGPT_AUDIT_CRITERIA_V03.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M04-C001/PL-0104_CODEX_LOG_V03.md

TASKS.md must authorize M04-BATCH-003 / READY / CODEX. Preserve all 16 accepted M04 children, accepted M03, and PL-0068 OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M05.

The production M04 architecture is already integrated. Do not add parallel camera/AR/motion/quality/session ownership. Close only the remaining frozen evidence/state gap.

## Mandatory remediation

1. Preserve the current production GuidedAutoCaptureService, health-gated backend and canonical accepted transaction.
2. Add integrated runtime/backend-call tests for quality reject, missing coverage target, pose ineligible, overlap blocked and health hard stop.
3. Prove in-flight duplicate suppression, exact cooldown boundary, rejected-candidate rearm and accepted-capture success.
4. For every blocked gate, prove the underlying still backend is not invoked unless the gate policy explicitly allows it.

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
