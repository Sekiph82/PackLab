# PL-0013 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0013 - Define independent auditor-AI responsibilities, minimum checks and PASS/FAIL criteria**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDITOR_AI_POLICY.md
All **24 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/AUDITOR_AI_POLICY.md and its new-file content was actually diff-reviewed.
8. Define ChatGPT auditor independence from builder claims is satisfied.
9. Require reading current TASKS.md before every audit decision is satisfied.
10. Require actual GitHub commit range, diff, changed-file and source inspection is satisfied.
11. Require disposition of every frozen mandatory criterion is satisfied.
12. Require architecture, negative-path, regression, test-sensitivity, security/privacy, determinism/provenance and scope checks as applicable is satisfied.
13. Define E3 independent evidence and label unrerun builder runtime evidence is satisfied.
14. Define PASS only when no mandatory criterion fails and no unresolved material defect remains is satisfied.
15. Define CHANGES_REQUIRED behavior with exact findings, retained task ID, tracker update and remediation is satisfied.
16. Define BLOCKED and OWNER_REQUIRED without manufactured closure is satisfied.
17. Define milestone-batch audits as separate child audits followed by milestone audit is satisfied.
18. Forbid auditor from silently changing requirements merely to pass implementation is satisfied.
19. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
20. Actual changed files match authorization and protected-file/privacy reviews pass.
21. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0013_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
22. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
23. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
24. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0013 unaccepted and M00 open.
