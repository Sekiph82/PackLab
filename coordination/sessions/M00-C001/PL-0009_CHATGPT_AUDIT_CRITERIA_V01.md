# PL-0009 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0009 - Define Definition of Done, audit gates and evidence requirements for every task**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/coordination/DEFINITION_OF_DONE.md
All **24 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/DEFINITION_OF_DONE.md and its new-file content was actually diff-reviewed.
8. Separate implementation-done from independently-audited-done is satisfied.
9. Require frozen prompt and matching frozen criteria before implementation is satisfied.
10. Require exact scope, required tests/checks, negative/boundary evidence when relevant, privacy/security and protected-file review is satisfied.
11. Require Codex log plus AWAITING_AUDIT or milestone-batch equivalent before independent audit is satisfied.
12. Require ChatGPT actual GitHub diff/source inspection rather than builder claims alone is satisfied.
13. Define AUDITED_PASS, CHANGES_REQUIRED/AUDITED_FAIL, BLOCKED and OWNER_REQUIRED consistently with AUDIT_POLICY.md is satisfied.
14. Require TASKS.md update only by ChatGPT after audit is satisfied.
15. Distinguish E1/E2/E3/E4 evidence and physical/device/owner limitations is satisfied.
16. Require regression and test-sensitivity review is satisfied.
17. Forbid checkbox completion without independent audit pass is satisfied.
18. Define milestone closure as all mandatory child tasks independently accepted is satisfied.
19. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
20. Actual changed files match authorization and protected-file/privacy reviews pass.
21. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0009_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
22. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
23. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
24. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0009 unaccepted and M00 open.
