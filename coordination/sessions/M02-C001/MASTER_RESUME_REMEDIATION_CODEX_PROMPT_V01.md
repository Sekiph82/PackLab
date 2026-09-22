# M02-C001 — Master Resume Remediation Codex Work Order V01

Repository: https://github.com/Sekiph82/PackLab
Milestone: M02 — PackScan Data Contract & Calibration

Blocking resume audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_RESUME_CHATGPT_AUDIT_V01.md

Master remediation criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_RESUME_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md

## Mission

Remediate exactly the ten failed audit-ready resume children before touching PL-0067.

## Authorization gate

TASKS.md must show:
- Current Milestone: M02
- Current Task: M02-RESUME-REMEDIATION-BATCH-001
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- Next action pointing to this master remediation prompt

Otherwise stop `TASK_STATE_MISMATCH`.

## Ordered remediation children

1. PL-0053
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0053_CHATGPT_AUDIT_CRITERIA_V02.md
2. PL-0056
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CHATGPT_AUDIT_CRITERIA_V02.md
3. PL-0057
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CHATGPT_AUDIT_CRITERIA_V02.md
4. PL-0058
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CHATGPT_AUDIT_CRITERIA_V02.md
5. PL-0060
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CHATGPT_AUDIT_CRITERIA_V02.md
6. PL-0061
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0061_CHATGPT_AUDIT_CRITERIA_V02.md
7. PL-0062
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_CRITERIA_V02.md
8. PL-0063
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0063_CHATGPT_AUDIT_CRITERIA_V02.md
9. PL-0064
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CHATGPT_AUDIT_CRITERIA_V02.md
10. PL-0066
   Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_CRITERIA_V02.md

Dependency order is intentional:
- PL-0057 precedes PL-0058.
- PL-0060 precedes PL-0061.
- PL-0062 precedes PL-0063/PL-0064.
- PL-0066 closes profile reuse before PL-0067 synthetic ground-truth reconciliation.

For each child:
1. synchronize safely;
2. read V01 history, blocking audit, V02 prompt and V02 criteria;
3. remediate only that child;
4. run focused negative/boundary/mutation validation plus relevant regressions;
5. commit/push implementation/evidence;
6. publish the separate V02 child log;
7. verify remote visibility and safe divergence;
8. continue only if builder validation is green.

If any child cannot satisfy its V02 criteria, stop the entire remediation batch. Do not skip it.

## Accepted children that must not be reopened

PL-0051, PL-0052, PL-0054, PL-0055, PL-0059 and PL-0065 are independently accepted. Preserve them.

## PL-0067 boundary

A prior PL-0067 implementation commit exists but has no accepted child log/audit and depends on open upstream calibration work.

During this remediation batch:
- do not publish/close PL-0067;
- do not treat its current implementation as accepted truth;
- after all ten remediations are audited PASS, PL-0067 must be reconciled/revalidated in its own handoff before independent audit.

## Hard boundaries

- Never edit TASKS.md.
- Never create ChatGPT audit files.
- Never self-audit.
- Never start PL-0067, PL-0068 or M03.
- Preserve accepted M00/M01/M02 contracts.
- No private Kenya scans, confidential supplier material, credentials, signing material, caches or owner-only data.
- Do not fabricate Swift/Xcode/device/physical evidence.

## Master remediation log

After all ten V02 child logs are published, create:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_RESUME_REMEDIATION_CODEX_LOG_V01.md

Index all ten children with prompt/criteria/log URLs, synchronized start, implementation/evidence commit, child-log commit, exact files, fixed defect, focused evidence, regressions and limitations.

End:
`REMEDIATION_BATCH_COMPLETED`
`AWAITING_MILESTONE_AUDIT`

Final response only:
`M02-C001 RESUME REMEDIATION`
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/MASTER_RESUME_REMEDIATION_CODEX_LOG_V01.md
`AWAITING_MILESTONE_AUDIT`
