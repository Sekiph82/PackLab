# PL-0013 - Codex Child Work Order V01
Task: **PL-0013 - Define independent auditor-AI responsibilities, minimum checks and PASS/FAIL criteria**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDITOR_AI_POLICY.md.

## Mandatory content
1. Define ChatGPT auditor independence from builder claims.
2. Require reading current TASKS.md before every audit decision.
3. Require actual GitHub commit range, diff, changed-file and source inspection.
4. Require disposition of every frozen mandatory criterion.
5. Require architecture, negative-path, regression, test-sensitivity, security/privacy, determinism/provenance and scope checks as applicable.
6. Define E3 independent evidence and label unrerun builder runtime evidence.
7. Define PASS only when no mandatory criterion fails and no unresolved material defect remains.
8. Define CHANGES_REQUIRED behavior with exact findings, retained task ID, tracker update and remediation.
9. Define BLOCKED and OWNER_REQUIRED without manufactured closure.
10. Define milestone-batch audits as separate child audits followed by milestone audit.
11. Forbid auditor from silently changing requirements merely to pass implementation.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/AUDITOR_AI_POLICY.md` plus `git diff -- coordination/AUDITOR_AI_POLICY.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
