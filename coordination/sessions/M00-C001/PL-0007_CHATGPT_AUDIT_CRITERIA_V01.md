# PL-0007 - ChatGPT Strict Child Audit Criteria V01
Task: **PL-0007 - Define source-control conventions: branches, commits, task IDs, pull-request naming and generated-file policy**
Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CODEX_PROMPT_V01.md
Artifact: https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/SOURCE_CONTROL_POLICY.md
All **21 criteria** are mandatory.

1. M00-BATCH-001/CODEX authorization existed before work.
2. Root TASKS.md was not edited by Codex.
3. No M01 task was started.
4. Repository freshness was checked and no unsafe Git operation was used.
5. No secret/private/confidential artifact entered public Git.
6. Prior prompt/log/audit history was not rewritten.
7. Canonical artifact exists at https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/SOURCE_CONTROL_POLICY.md and its new-file content was actually diff-reviewed.
8. Define GitHub main as canonical integration truth and distinguish current direct-main AI workflow from future branch/PR use is satisfied.
9. Define branch naming tied to PL task IDs, commit-message conventions, and future PR title/naming conventions is satisfied.
10. Define generated-file classes: source artifacts, regenerable intermediates, local caches, safe fixtures is satisfied.
11. Prohibit private scans, Kenya assets, secrets, signing material, local environments and ephemeral reconstruction outputs from public Git is satisfied.
12. Defer concrete Git LFS configuration to PL-0023 while defining decision principles is satisfied.
13. Define normal-session Git safety with no force-push/reset/rebase/destructive cleanup unless explicitly owner-authorized is satisfied.
14. Define task IDs as workflow identifiers, not semantic versions is satisfied.
15. Cross-reference TASKS.md, AGENTS.md, MILESTONE_BATCH_PROTOCOL.md and VERSIONING_POLICY.md without becoming live state is satisfied.
16. git diff --check passed and git diff -- TASKS.md is empty for builder changes.
17. Actual changed files match authorization and protected-file/privacy reviews pass.
18. Child log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M00-C001/PL-0007_CODEX_LOG_V01.md and links the full prompt/criteria URLs.
19. Child log records child start, implementation/evidence commit, validations, failures/fixes, scope/privacy and push evidence.
20. Child log does not self-assign PASS or predeclare its future log SHA and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub diff/source matches the log claims.

## Closure
ChatGPT independently inspects actual GitHub commit range, changed files, artifact semantics, log, architecture, privacy/security, scope and regressions. Any failed mandatory criterion keeps PL-0007 unaccepted and M00 open.
