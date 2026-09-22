# PL-0046 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0046_CHATGPT_AUDIT_V01.md

All **22 criteria** are mandatory.

1. TASKS.md authorized M02-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0051, later M02 child, or M03 work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Replace the generic unconstrained measurement contract with field-specific constraints for focal length, exposure, ISO and white balance is satisfied.
9. Require focal length unit mm and a positive finite value when present is satisfied.
10. Require exposure unit s and a positive finite value when present is satisfied.
11. Require the frozen ISO unit token and an integer valid positive range when present is satisfied.
12. Require white-balance unit K and a physically valid positive range when present is satisfied.
13. Do not rely on nonstandard JSON-Schema keywords such as finite for portability is satisfied.
14. Preserve explicit available/estimated/unavailable/not_recorded states and prohibit values for unavailable/not_recorded states is satisfied.
15. Add negative fixtures/tests for wrong units, zero/negative values and fractional ISO is satisfied.
16. Still-valid original V01 behavior remains intact.
17. Focused tests are sensitivity-bearing and would fail on the pre-remediation defect.
18. Relevant accepted M00/M01 behavior remains unregressed.
19. git diff --check passes and builder TASKS.md diff is empty.
20. Platform/device/physical evidence boundaries are truthful.
21. PL-0046_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
22. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
