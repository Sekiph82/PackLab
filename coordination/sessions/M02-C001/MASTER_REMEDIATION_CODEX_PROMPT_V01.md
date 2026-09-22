# M02-C001 — Master Remediation Codex Work Order V01

Repository: https://github.com/Sekiph82/PackLab
Milestone: M02 — PackScan Data Contract & Calibration

Prior master audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_CHATGPT_AUDIT_V01.md

Master remediation criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md

## Mission

Remediate only the seven attempted M02 children before resuming the milestone. Do not start PL-0051.

## Authorization gate

TASKS.md must show:
- Current Milestone: M02
- Current Task: M02-REMEDIATION-BATCH-001
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- Next action pointing to this master remediation prompt

Otherwise stop `TASK_STATE_MISMATCH`.

## Ordered children

1. PL-0044: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CHATGPT_AUDIT_CRITERIA_V02.md
2. PL-0045: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0045_CHATGPT_AUDIT_CRITERIA_V02.md
3. PL-0046: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CHATGPT_AUDIT_CRITERIA_V02.md
4. PL-0047: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CHATGPT_AUDIT_CRITERIA_V02.md
5. PL-0048: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_CRITERIA_V02.md
6. PL-0049: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CHATGPT_AUDIT_CRITERIA_V02.md
7. PL-0050: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0050_CHATGPT_AUDIT_CRITERIA_V02.md

For each child:
1. synchronize safely;
2. read V01 history, V02 prompt/criteria and blocking audit;
3. remediate only the child scope;
4. run focused + regression validation;
5. commit/push implementation/evidence;
6. publish the separate V02 child log;
7. verify remote visibility and safe divergence;
8. continue only if builder validation is green.

If any child cannot satisfy the frozen criteria, stop the batch. Do not skip it and do not start PL-0051.

## Hard boundaries

- Never edit TASKS.md.
- Never create ChatGPT audit verdicts.
- Never self-audit.
- Never start PL-0051 or M03.
- Preserve M00/M01 accepted architecture.
- No private scan/confidential supplier/credential/signing/cache material.
- Do not fabricate native/device/physical evidence.

## Master log

After all seven V02 child logs are published, create:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

Index every child with prompt/criteria/log URLs, start commit, implementation/evidence commit, log commit, files changed, fixed defect, focused tests, regressions and limitations.

End:
`REMEDIATION_BATCH_COMPLETED`
`AWAITING_MILESTONE_AUDIT`

Final response only:
`M02-C001 REMEDIATION`
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md
`AWAITING_MILESTONE_AUDIT`
