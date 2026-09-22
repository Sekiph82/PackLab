# PL-0047 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0047_CHATGPT_AUDIT_V01.md

All **21 criteria** are mandatory.

1. TASKS.md authorized M02-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0051, later M02 child, or M03 work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Make distortion branches explicit and machine-enforced by model is satisfied.
9. For model none, require empty coefficient_order and empty coefficients is satisfied.
10. For fisheye, require exact OpenCV order [k1,k2,k3,k4] and exactly four coefficients is satisfied.
11. For Brown-Conrady, freeze one explicitly named supported coefficient order/version and require matching coefficient count; do not accept arbitrary strings or lengths is satisfied.
12. Require coefficients whenever a non-none model is selected is satisfied.
13. Preserve the existing matrix/origin/dimension-policy/provenance rules is satisfied.
14. Add negative fixtures/tests for wrong order, missing coefficients, mismatched lengths and illegal coefficients for model none is satisfied.
15. Still-valid original V01 behavior remains intact.
16. Focused tests are sensitivity-bearing and would fail on the pre-remediation defect.
17. Relevant accepted M00/M01 behavior remains unregressed.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform/device/physical evidence boundaries are truthful.
20. PL-0047_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
