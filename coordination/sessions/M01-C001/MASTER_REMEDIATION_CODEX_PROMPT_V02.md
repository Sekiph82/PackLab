# M01-C001 — Master Remediation Codex Work Order V02

Repository: https://github.com/Sekiph82/PackLab
Milestone: M01 — Monorepo & Development Foundations

Prior master remediation audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_V01.md

Master V02 criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V02.md

## Mission

Remediate **only the four remaining M01 findings**. Do not reopen accepted children and do not start M02.

## Authorization gate

TASKS.md must show:
- Current Milestone: M01
- Current Task: M01-REMEDIATION-BATCH-002
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- Next action pointing to this master prompt

Otherwise stop with `TASK_STATE_MISMATCH`.

## Order

1. PL-0026: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V03.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_CRITERIA_V03.md
2. PL-0031: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V03.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_CRITERIA_V03.md
3. PL-0035: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V03.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V03.md
4. PL-0043: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V03.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V03.md

For each child: synchronize safely, execute only its V03 work order, validate fully, commit/push implementation/evidence, publish its V03 log, verify remote 0 0, then continue. If any child cannot satisfy its criteria, stop the batch rather than skipping it.

Never edit TASKS.md. Never create ChatGPT audit files. Never self-audit.

After all four V03 logs are published, create:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md

Index all four children with prompt/criteria/log URLs, start and implementation/evidence commits, files changed, defect fixed, validations and limitations.

End:
`REMEDIATION_BATCH_COMPLETED`
`AWAITING_MILESTONE_AUDIT`

Final response only:
`M01-C001 REMEDIATION V02`
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CODEX_LOG_V02.md
`AWAITING_MILESTONE_AUDIT`
