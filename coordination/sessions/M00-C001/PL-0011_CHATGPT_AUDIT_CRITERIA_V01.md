# PL-0011 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0011 - Validate the canonical session workflow**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0011_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/coordination/SESSION_WORKFLOW_VALIDATION.md
All **23 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/SESSION_WORKFLOW_VALIDATION.md and its new-file content was actually diff-reviewed.
8. Validate TASKS.md -> frozen prompt/criteria -> Codex implementation/log -> ChatGPT audit -> ChatGPT TASKS.md update using existing repository evidence is satisfied.
9. Use completed PL-0001..PL-0005 cycles as historical evidence and describe PL-0006 history accurately is satisfied.
10. Document milestone-batch as execution batching only, not acceptance batching is satisfied.
11. Show Codex cannot edit TASKS.md or self-audit is satisfied.
12. Show ChatGPT is sole lifecycle/closure writer is satisfied.
13. Show CHANGES_REQUIRED preserves task identity and evidence history is satisfied.
14. Show batch stop conditions prevent silent skipping is satisfied.
15. Define expected artifact naming and full GitHub-link handoff behavior is satisfied.
16. Record limitations when local runtime commands cannot be independently rerun is satisfied.
17. Do not create a second current-task tracker is satisfied.
18. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
19. Actual changed files match authorization and protected-file/privacy reviews pass.
20. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0011_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
21. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
22. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
23. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0011 unaccepted and M00 open.
