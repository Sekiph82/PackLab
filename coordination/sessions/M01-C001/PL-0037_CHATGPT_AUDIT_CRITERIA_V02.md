# PL-0037 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CODEX_PROMPT_V02.md
Prior audit evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CHATGPT_AUDIT_V02.md

All **23 criteria** are mandatory.

1. Root TASKS.md authorized the M01 remediation batch / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 task or unrelated future product work was started.
5. No secret/private scan/confidential supplier/signing material/cache was committed.
6. Actual changed files are within the authorized remediation scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is actually corrected, not merely documented.
8. Preserve the canonical NextLevel repository and exact 0.19.1 pin is satisfied.
9. Create the PBXBuildFile whose productRef points to the NextLevel XCSwiftPackageProductDependency and add it to the PackLabCapture Frameworks build phase is satisfied.
10. Keep the target packageProductDependencies and project packageReferences coherent is satisfied.
11. Add no unrelated Swift dependency and keep NextLevel behind PackLab-owned service boundaries is satisfied.
12. Correct the documentation attribution: the pinned 0.19.1 Package.swift declares iOS 16; do not claim that fact comes from README migration prose is satisfied.
13. Add static checks for URL, exact version, product dependency, productRef build file and Frameworks-phase membership; do not fabricate Xcode build evidence is satisfied.
14. Original task behavior not implicated by the defect remains intact.
15. Relevant sibling M01 regressions remain intact.
16. Focused tests/static checks are meaningful and would fail on the pre-remediation defect.
17. git diff --check passes and builder TASKS.md diff is empty.
18. Protected-file/privacy/security review passes.
19. Platform-specific evidence is truthful and unavailable native/device evidence is not fabricated.
20. Remediation log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0037_CODEX_LOG_V02.md and links prompt/criteria/audit evidence.
21. Log records start/implementation evidence, files changed, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
22. Log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
23. Actual GitHub diff/source/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently re-audits the full task against this remediation criteria plus the still-applicable original criteria. A PASS may close this task for M01 only if no new material regression is found.
