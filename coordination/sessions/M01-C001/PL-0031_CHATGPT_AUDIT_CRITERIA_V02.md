# PL-0031 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V02.md
Prior audit evidence: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_V02.md

All **22 criteria** are mandatory.

1. Root TASKS.md authorized the M01 remediation batch / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 task or unrelated future product work was started.
5. No secret/private scan/confidential supplier/signing material/cache was committed.
6. Actual changed files are within the authorized remediation scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is actually corrected, not merely documented.
8. Enable strict unknown-marker validation using strict_markers=true or --strict-markers in canonical pytest configuration is satisfied.
9. Keep unit, integration and slow registered is satisfied.
10. Keep slow excluded by default and explicitly selectable is satisfied.
11. Add a regression that an intentionally unknown marker fails collection/configuration while known markers still work is satisfied.
12. Update documentation so the claimed strict-marker behavior matches actual configuration is satisfied.
13. Original task behavior not implicated by the defect remains intact.
14. Relevant sibling M01 regressions remain intact.
15. Focused tests/static checks are meaningful and would fail on the pre-remediation defect.
16. git diff --check passes and builder TASKS.md diff is empty.
17. Protected-file/privacy/security review passes.
18. Platform-specific evidence is truthful and unavailable native/device evidence is not fabricated.
19. Remediation log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_LOG_V02.md and links prompt/criteria/audit evidence.
20. Log records start/implementation evidence, files changed, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
21. Log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
22. Actual GitHub diff/source/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently re-audits the full task against this remediation criteria plus the still-applicable original criteria. A PASS may close this task for M01 only if no new material regression is found.
