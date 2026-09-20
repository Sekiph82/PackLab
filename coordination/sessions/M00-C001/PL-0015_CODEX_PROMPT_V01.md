# PL-0015 - Codex Child Work Order V01
Task: **PL-0015 - Define Codex implementation-log and AWAITING_AUDIT handoff format**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0015_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0015_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0015_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/CODEX_LOG_CONTRACT.md.

## Mandatory content
1. Define required log metadata: cycle/task, full prompt URL, full criteria URL, synchronized start commit and implementation/evidence commit.
2. Require files read and files changed.
3. Require exact tests/checks with expected result, failure condition and actual result.
4. Require failure/fix chronology.
5. Require negative/boundary/regression evidence where applicable.
6. Require secrets/privacy and scope review.
7. Require push/remote visibility evidence.
8. Require known limitations and unverified assumptions.
9. Forbid self-referential future log-containing SHA claims.
10. Define single-task AWAITING_AUDIT handoff.
11. Define child READY_FOR_INDEPENDENT_AUDIT plus master AWAITING_MILESTONE_AUDIT for milestone batches.
12. Keep CODEX_LOG_TEMPLATE.md as helper evidence, not live project state.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/CODEX_LOG_CONTRACT.md` plus `git diff -- coordination/CODEX_LOG_CONTRACT.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0015_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
