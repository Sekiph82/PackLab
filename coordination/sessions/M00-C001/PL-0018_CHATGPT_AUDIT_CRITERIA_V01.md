# PL-0018 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0018 - Add protocol for architecture changes that require an ADR before implementation**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/coordination/ARCHITECTURE_CHANGE_PROTOCOL.md
All **23 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/ARCHITECTURE_CHANGE_PROTOCOL.md and its new-file content was actually diff-reviewed.
8. Define architecture change versus bounded implementation detail is satisfied.
9. Require ADR before changes to canonical boundaries such as monorepo topology, PackScan authority/schema philosophy, Scan Mesh/Scan Master/Design Model separation, units/coordinate-system truth, major engine ownership or live tracking authority is satisfied.
10. Reference the existing ADR process and ADR-0001 is satisfied.
11. Define ADR_REQUIRED stop behavior for builders is satisfied.
12. Forbid opportunistic ADR creation by Codex when prompt requires stopping for ChatGPT/owner decision is satisfied.
13. Define when ChatGPT may issue an ADR task/work order after evidence review is satisfied.
14. Require approved ADR linkage in later implementing prompts is satisfied.
15. Define milestone-batch behavior: architecture contradiction stops the batch before later children is satisfied.
16. Preserve TASKS.md as sole live tracker and GitHub main as repository truth is satisfied.
17. Do not implement any architecture change in this task is satisfied.
18. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
19. Actual changed files match authorization and protected-file/privacy reviews pass.
20. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0018_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
21. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
22. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
23. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0018 unaccepted and M00 open.
