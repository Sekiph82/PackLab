# PL-0012 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0012 - Define builder-AI responsibilities and forbidden actions**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/coordination/BUILDER_AI_POLICY.md
All **23 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/BUILDER_AI_POLICY.md and its new-file content was actually diff-reviewed.
8. Define builder responsibilities: synchronize, read authority, implement frozen scope, test, log, commit/push and hand off is satisfied.
9. Forbid builder edits to TASKS.md lifecycle state is satisfied.
10. Forbid builder-created ChatGPT audits or self-assigned AUDITED_PASS is satisfied.
11. Forbid task reprioritization, task-ID invention, silent scope expansion and future-task implementation is satisfied.
12. Forbid destructive Git operations outside explicit owner authorization is satisfied.
13. Forbid secret/private asset publication is satisfied.
14. Require STOP on authorization mismatch, unsafe divergence, architecture contradiction, blocker or owner decision is satisfied.
15. Define builder evidence as E1/E2, not independent E3 is satisfied.
16. Define milestone-batch exception: sequential children only under explicit master authorization and stop on failed child validation is satisfied.
17. Require truthful failure/fix recording and forbid fabricated test/device evidence is satisfied.
18. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
19. Actual changed files match authorization and protected-file/privacy reviews pass.
20. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0012_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
21. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
22. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
23. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0012 unaccepted and M00 open.
