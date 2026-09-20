# PL-0014 - Codex Child Work Order V01
Task: **PL-0014 - Define audit evidence format including commands, test output, inspected files and residual risks**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0014_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0014_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0014_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_EVIDENCE_FORMAT.md.

## Mandatory content
1. Define evidence records with criterion/task reference, evidence level, source/command, expected result, failure condition, actual result and disposition.
2. Define concise command/output recording without leaking secrets.
3. Define inspected files, line ranges, diffs and commit SHA recording.
4. Distinguish builder E1/E2 evidence from auditor E3 evidence.
5. Define negative-test, regression and test-sensitivity evidence.
6. Define residual risk and limitation fields.
7. Define privacy/security redaction rules.
8. Define physical/device/owner E4 evidence references without fabricating independent reproduction.
9. Define child-task and milestone-batch evidence indexing.
10. Do not become a live tracker.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/AUDIT_EVIDENCE_FORMAT.md` plus `git diff -- coordination/AUDIT_EVIDENCE_FORMAT.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0014_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
