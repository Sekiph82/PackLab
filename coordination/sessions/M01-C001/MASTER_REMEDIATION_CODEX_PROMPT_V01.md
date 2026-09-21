# M01-C001 — Master Remediation Codex Work Order V01

Repository: https://github.com/Sekiph82/PackLab
Milestone: M01 — Monorepo & Development Foundations

Master audit:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_CHATGPT_AUDIT_V01.md

Master remediation criteria:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CHATGPT_AUDIT_CRITERIA_V01.md

## Mission

Execute all M01 remediation children sequentially. These are the only open M01 findings. Preserve all fourteen accepted sibling tasks and do not start M02.

The remediation order is dependency-safe rather than purely numeric. PL-0036 current-state revalidation runs last so it validates the final iOS project graph after SPM/diagnostics/XCTest repairs.

## Authorization gate

Before work, root TASKS.md must explicitly authorize:
- Current Milestone: M01
- Current Task: M01-REMEDIATION-BATCH-001
- Current Task Status: CHANGES_REQUIRED
- Required Actor: CODEX
- Next action pointing to this master remediation prompt

Otherwise stop TASK_STATE_MISMATCH.

## Ordered remediation children

1. PL-0024: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0024_CHATGPT_AUDIT_CRITERIA_V02.md
2. PL-0025: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_CRITERIA_V02.md
3. PL-0026: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_CRITERIA_V02.md
4. PL-0030: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0030_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0030_CHATGPT_AUDIT_CRITERIA_V02.md
5. PL-0031: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_CRITERIA_V02.md
6. PL-0034: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0034_CHATGPT_AUDIT_CRITERIA_V02.md
7. PL-0035: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_CRITERIA_V02.md
8. PL-0037: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CHATGPT_AUDIT_CRITERIA_V02.md
9. PL-0041: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0041_CHATGPT_AUDIT_CRITERIA_V02.md
10. PL-0043: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_CRITERIA_V02.md
11. PL-0036: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CODEX_PROMPT_V02.md
   Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0036_CHATGPT_AUDIT_CRITERIA_V02.md

For each child:
1. refresh/synchronize safely;
2. read its V02 prompt, criteria and prior audit;
3. remediate only that task;
4. run full focused/regression validation;
5. commit/push implementation/evidence;
6. publish coordination/sessions/M01-C001/PL-xxxx_CODEX_LOG_V02.md;
7. verify remote visibility and safe 0 0 state;
8. continue only if the child is validation-green.

If a child cannot satisfy its requirements, stop the whole remediation batch. Do not skip it.

## Hard boundaries

- Never edit TASKS.md.
- Never create ChatGPT audit artifacts.
- Never self-audit.
- Never start M02.
- Preserve accepted M00 and accepted M01 siblings.
- Never fabricate native Xcode/device/CUDA evidence.
- Keep public-repository privacy/security boundaries.

## Master remediation log

After all remediation child logs are published, create:

https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md

Index all 11 children with prompt/criteria/log URLs, synchronized start, implementation/evidence commit, log commit, files changed, defect fixed, regression results and limitations.

End with:
`REMEDIATION_BATCH_COMPLETED`
`AWAITING_MILESTONE_AUDIT`

Final response only:
`M01-C001 REMEDIATION`
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/MASTER_REMEDIATION_CODEX_LOG_V01.md
`AWAITING_MILESTONE_AUDIT`
