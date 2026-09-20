# PL-0009 - Codex Child Work Order V01
Task: **PL-0009 - Define Definition of Done, audit gates and evidence requirements for every task**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/DEFINITION_OF_DONE.md.

## Mandatory content
1. Separate implementation-done from independently-audited-done.
2. Require frozen prompt and matching frozen criteria before implementation.
3. Require exact scope, required tests/checks, negative/boundary evidence when relevant, privacy/security and protected-file review.
4. Require Codex log plus AWAITING_AUDIT or milestone-batch equivalent before independent audit.
5. Require ChatGPT actual GitHub diff/source inspection rather than builder claims alone.
6. Define AUDITED_PASS, CHANGES_REQUIRED/AUDITED_FAIL, BLOCKED and OWNER_REQUIRED consistently with AUDIT_POLICY.md.
7. Require TASKS.md update only by ChatGPT after audit.
8. Distinguish E1/E2/E3/E4 evidence and physical/device/owner limitations.
9. Require regression and test-sensitivity review.
10. Forbid checkbox completion without independent audit pass.
11. Define milestone closure as all mandatory child tasks independently accepted.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/DEFINITION_OF_DONE.md` plus `git diff -- coordination/DEFINITION_OF_DONE.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
