# PL-0025 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_PROMPT_V02.md
Prior audit evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CHATGPT_AUDIT_V02.md

All **23 criteria** are mandatory.

1. Root TASKS.md authorized the M01 remediation batch / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 task or unrelated future product work was started.
5. No secret/private scan/confidential supplier/signing material/cache was committed.
6. Actual changed files are within the authorized remediation scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is actually corrected, not merely documented.
8. Make the root task runner the real single M01 entry point for bootstrap, test, lint, type-check, diagnostics and build-oriented commands is satisfied.
9. On Windows, bootstrap must safely dispatch scripts/bootstrap_windows.ps1 using an argument-array subprocess; on unsupported platforms report a clear nonzero/deferred state until their bootstrap exists is satisfied.
10. Test, lint and type-check must run through the locked uv project environment and must not depend on globally installed pytest/Ruff/mypy or shell activation is satisfied.
11. Diagnostics must remain safe and direct; build remains explicitly deferred until its owning milestone is satisfied.
12. Preserve shell=False/argument-array execution and child exit-code propagation is satisfied.
13. Add focused tests for command construction, Windows bootstrap dispatch, uv missing/unavailable handling, exit propagation, and no global PATH dependency is satisfied.
14. Original task behavior not implicated by the defect remains intact.
15. Relevant sibling M01 regressions remain intact.
16. Focused tests/static checks are meaningful and would fail on the pre-remediation defect.
17. git diff --check passes and builder TASKS.md diff is empty.
18. Protected-file/privacy/security review passes.
19. Platform-specific evidence is truthful and unavailable native/device evidence is not fabricated.
20. Remediation log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0025_CODEX_LOG_V02.md and links prompt/criteria/audit evidence.
21. Log records start/implementation evidence, files changed, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
22. Log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
23. Actual GitHub diff/source/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently re-audits the full task against this remediation criteria plus the still-applicable original criteria. A PASS may close this task for M01 only if no new material regression is found.
