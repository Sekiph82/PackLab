# PL-0016 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0016 - Add protocol for failed audits: reopen same task, preserve checkbox, remediate findings, re-audit**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/coordination/FAILED_AUDIT_PROTOCOL.md
All **23 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/FAILED_AUDIT_PROTOCOL.md and its new-file content was actually diff-reviewed.
8. Keep the same permanent PL task ID after failure is satisfied.
9. Keep the task unchecked until independent pass is satisfied.
10. Preserve prior prompts, criteria, logs and audits as immutable evidence is satisfied.
11. Version remediation prompts/criteria instead of overwriting prior artifacts is satisfied.
12. Require exact failure findings and bounded remediation scope is satisfied.
13. Require TASKS.md to show CHANGES_REQUIRED and next actor/action is satisfied.
14. Require builder to fix only authorized findings and rerun relevant regressions is satisfied.
15. Require fresh independent audit of remediation and integrity of previously accepted behavior is satisfied.
16. Define milestone-batch behavior: stop at failed child validation/audit frontier and do not discard accepted earlier child audits is satisfied.
17. Forbid false completion or skipping to the next task is satisfied.
18. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
19. Actual changed files match authorization and protected-file/privacy reviews pass.
20. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0016_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
21. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
22. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
23. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0016 unaccepted and M00 open.
