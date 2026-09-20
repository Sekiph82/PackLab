# PL-0008 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0008 - Define secrets policy so Apple credentials, signing certificates and tokens never enter Git**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/docs/security/SECRETS_POLICY.md
All **23 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/docs/security/SECRETS_POLICY.md and its new-file content was actually diff-reviewed.
8. Define secret classes including GitHub/API tokens, Apple credentials/session data, signing private keys/certificates, provisioning-sensitive material, passwords and cloud credentials is satisfied.
9. Prohibit secrets in Git history, tracked config, logs, screenshots, fixtures, prompts copied into repo, generated artifacts and examples is satisfied.
10. Define safe environment-variable, OS keychain and CI-secret principles without implementing them is satisfied.
11. Define public-safe placeholder syntax that cannot be mistaken for a real credential is satisfied.
12. Define accidental-secret response: stop, revoke/rotate, audit affected history and use an approved purge process rather than merely deleting the latest file is satisfied.
13. Distinguish public certificate material from private signing keys/provisioning-sensitive material is satisfied.
14. Define local .env/config principles while deferring concrete .gitignore to PL-0021 is satisfied.
15. Define redaction rules for Codex logs and audits is satisfied.
16. Treat private Kenya scans, supplier documents and proprietary artwork as confidential protected data is satisfied.
17. Do not implement signing, CI, keychain integration or credential storage is satisfied.
18. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
19. Actual changed files match authorization and protected-file/privacy reviews pass.
20. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0008_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
21. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
22. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
23. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0008 unaccepted and M00 open.
