# PL-0018 - Codex Child Work Order V01
Task: **PL-0018 - Add protocol for architecture changes that require an ADR before implementation**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/ARCHITECTURE_CHANGE_PROTOCOL.md.

## Mandatory content
1. Define architecture change versus bounded implementation detail.
2. Require ADR before changes to canonical boundaries such as monorepo topology, PackScan authority/schema philosophy, Scan Mesh/Scan Master/Design Model separation, units/coordinate-system truth, major engine ownership or live tracking authority.
3. Reference the existing ADR process and ADR-0001.
4. Define ADR_REQUIRED stop behavior for builders.
5. Forbid opportunistic ADR creation by Codex when prompt requires stopping for ChatGPT/owner decision.
6. Define when ChatGPT may issue an ADR task/work order after evidence review.
7. Require approved ADR linkage in later implementing prompts.
8. Define milestone-batch behavior: architecture contradiction stops the batch before later children.
9. Preserve TASKS.md as sole live tracker and GitHub main as repository truth.
10. Do not implement any architecture change in this task.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N coordination/ARCHITECTURE_CHANGE_PROTOCOL.md` plus `git diff -- coordination/ARCHITECTURE_CHANGE_PROTOCOL.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
