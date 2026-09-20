# PL-0016 - Codex Child Work Order V01
Task: **PL-0016 - Add protocol for failed audits: reopen same task, preserve checkbox, remediate findings, re-audit**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/FAILED_AUDIT_PROTOCOL.md.

## Mandatory content
1. Keep the same permanent PL task ID after failure.
2. Keep the task unchecked until independent pass.
3. Preserve prior prompts, criteria, logs and audits as immutable evidence.
4. Version remediation prompts/criteria instead of overwriting prior artifacts.
5. Require exact failure findings and bounded remediation scope.
6. Require TASKS.md to show CHANGES_REQUIRED and next actor/action.
7. Require builder to fix only authorized findings and rerun relevant regressions.
8. Require fresh independent audit of remediation and integrity of previously accepted behavior.
9. Define milestone-batch behavior: stop at failed child validation/audit frontier and do not discard accepted earlier child audits.
10. Forbid false completion or skipping to the next task.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/FAILED_AUDIT_PROTOCOL.md` plus `git diff -- coordination/FAILED_AUDIT_PROTOCOL.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
