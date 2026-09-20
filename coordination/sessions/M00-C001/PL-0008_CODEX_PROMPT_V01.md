# PL-0008 - Codex Child Work Order V01
Task: **PL-0008 - Define secrets policy so Apple credentials, signing certificates and tokens never enter Git**

Repository: https://github.com/Sekiph82/PackLab
Master: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/MASTER_CODEX_PROMPT_V01.md
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CHATGPT_AUDIT_CRITERIA_V01.md
Log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CODEX_LOG_V01.md

Read https://github.com/Sekiph82/PackLab/blob/main/TASKS.md, https://github.com/Sekiph82/PackLab/blob/main/AGENTS.md, https://github.com/Sekiph82/PackLab/blob/main/coordination/MILESTONE_BATCH_PROTOCOL.md and https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDIT_POLICY.md. TASKS.md must still authorize M00-BATCH-001 / CODEX. Never edit TASKS.md.

## Objective
Create https://github.com/Sekiph82/PackLab/blob/main/docs/security/SECRETS_POLICY.md.

## Mandatory content
1. Define secret classes including GitHub/API tokens, Apple credentials/session data, signing private keys/certificates, provisioning-sensitive material, passwords and cloud credentials.
2. Prohibit secrets in Git history, tracked config, logs, screenshots, fixtures, prompts copied into repo, generated artifacts and examples.
3. Define safe environment-variable, OS keychain and CI-secret principles without implementing them.
4. Define public-safe placeholder syntax that cannot be mistaken for a real credential.
5. Define accidental-secret response: stop, revoke/rotate, audit affected history and use an approved purge process rather than merely deleting the latest file.
6. Distinguish public certificate material from private signing keys/provisioning-sensitive material.
7. Define local .env/config principles while deferring concrete .gitignore to PL-0021.
8. Define redaction rules for Codex logs and audits.
9. Treat private Kenya scans, supplier documents and proprietary artwork as confidential protected data.
10. Do not implement signing, CI, keychain integration or credential storage.

## Validation and scope
Run and record `git diff --check`, `git diff -- TASKS.md`, `git status --short --branch`, explicit checks for every requirement, exact changed-file review, protected-file review and privacy/security review.
Review the new file with `git add -N docs/security/SECRETS_POLICY.md` plus `git diff -- docs/security/SECRETS_POLICY.md`, or equivalent staged review.
Do not start the next child until this child is validation-green and its log is pushed. Do not start M01. Stop the whole batch on blocker, authorization mismatch, unsafe divergence, privacy risk or ADR_REQUIRED.

## Log
Create https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CODEX_LOG_V01.md. Record full prompt/criteria URLs, child start, implementation/evidence commit, files read/changed, validations with expected/failure/actual results, failures/fixes, scope/privacy checks, push evidence and limitations. End `READY_FOR_INDEPENDENT_AUDIT`. Do not self-audit or predeclare the future log commit SHA.
