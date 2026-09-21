# PL-0026 — ChatGPT Strict Remediation Audit Criteria V03

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_PROMPT_V03.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CHATGPT_AUDIT_V02.md

All **23 criteria** are mandatory.

1. Root TASKS.md authorized M01-REMEDIATION-BATCH-002 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 or unrelated future work was started.
5. No secret/private/confidential/signing/cache artifact was committed.
6. Changed files stay within the authorized V03 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is corrected, not merely described.
8. Preserve the corrected default Windows cache/work/data layout and existing macOS/Linux defaults is satisfied.
9. Preserve PACKLAB_CACHE_ROOT and PACKLAB_DATA_ROOT overrides, but never silently accept an unsafe cache/data pair is satisfied.
10. Reject with an actionable error when cache and durable data are equal, data is beneath cache, or cache is beneath data. Workspace may remain beneath cache is satisfied.
11. Enforce the invariant in the public path-resolution flow used by PackLab, not only in documentation is satisfied.
12. Add temporary-path tests for equal roots, both ancestor/descendant directions, safe siblings, defaults and overrides. No real profile paths is satisfied.
13. Update CACHE_POLICY.md to describe the enforced non-overlap invariant is satisfied.
14. Still-valid original and V02 behavior remains intact.
15. Focused regression evidence would fail on the audited pre-V03 defect.
16. Relevant accepted sibling M01 behavior remains unregressed.
17. git diff --check passes and builder TASKS.md diff is empty.
18. Protected-file/privacy/security review passes.
19. Platform evidence is truthful; unavailable native/device evidence is not fabricated.
20. V03 Codex log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0026_CODEX_LOG_V03.md and links the V03 prompt/criteria and blocking audit.
21. V03 log records start/implementation evidence, exact files, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
22. V03 log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
23. Actual GitHub source/diff/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently audits the actual V03 implementation/source/log. This task closes only if every criterion passes.
