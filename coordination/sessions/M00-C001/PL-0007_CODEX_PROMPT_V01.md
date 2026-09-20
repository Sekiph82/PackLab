# PL-0007 - Codex Child Work Order V01
Task: **PL-0007 - Define source-control conventions: branches, commits, task IDs, pull-request naming and generated-file policy**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/SOURCE_CONTROL_POLICY.md.

## Mandatory content
1. Define GitHub main as canonical integration truth and distinguish current direct-main AI workflow from future branch/PR use.
2. Define branch naming tied to PL task IDs, commit-message conventions, and future PR title/naming conventions.
3. Define generated-file classes: source artifacts, regenerable intermediates, local caches, safe fixtures.
4. Prohibit private scans, Kenya assets, secrets, signing material, local environments and ephemeral reconstruction outputs from public Git.
5. Defer concrete Git LFS configuration to PL-0023 while defining decision principles.
6. Define normal-session Git safety with no force-push/reset/rebase/destructive cleanup unless explicitly owner-authorized.
7. Define task IDs as workflow identifiers, not semantic versions.
8. Cross-reference TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md and VERSIONING_POLICY.md without becoming live state.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N docs/architecture/SOURCE_CONTROL_POLICY.md` plus `git diff -- docs/architecture/SOURCE_CONTROL_POLICY.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
