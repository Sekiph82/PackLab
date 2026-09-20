# PL-0012 - Codex Child Work Order V01
Task: **PL-0012 - Define builder-AI responsibilities and forbidden actions**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/BUILDER_AI_POLICY.md.

## Mandatory content
1. Define builder responsibilities: synchronize, read authority, implement frozen scope, test, log, commit/push and hand off.
2. Forbid builder edits to TASKS.md lifecycle state.
3. Forbid builder-created ChatGPT audits or self-assigned AUDITED_PASS.
4. Forbid task reprioritization, task-ID invention, silent scope expansion and future-task implementation.
5. Forbid destructive Git operations outside explicit owner authorization.
6. Forbid secret/private asset publication.
7. Require STOP on authorization mismatch, unsafe divergence, architecture contradiction, blocker or owner decision.
8. Define builder evidence as E1/E2, not independent E3.
9. Define milestone-batch exception: sequential children only under explicit master authorization and stop on failed child validation.
10. Require truthful failure/fix recording and forbid fabricated test/device evidence.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/BUILDER_AI_POLICY.md` plus `git diff -- coordination/BUILDER_AI_POLICY.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
