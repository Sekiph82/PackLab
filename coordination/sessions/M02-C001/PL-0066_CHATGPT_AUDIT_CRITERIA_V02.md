# PL-0066 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0066_CHATGPT_AUDIT_V01.md

All **21 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Make the persisted calibration-profile schema the canonical structural validation source before compatibility/reuse decisions, or use one equivalent generated validator without weaker duplicate rules is satisfied.
9. A reusable measured/candidate profile must satisfy the required owner/native-capture/physical-measurement provenance states; unavailable provenance must fail closed is satisfied.
10. Parse/validate timestamps as real RFC3339/UTC date-times rather than suffix-only checks is satisfied.
11. Enforce positive resolution dimensions, required non-empty key fields, known resolution policy/schema version and all persisted confidence/RMSE/view-count ranges before reuse is satisfied.
12. Preserve exact-match and explicitly allowed same-aspect resolution compatibility behavior only after structural/provenance validation succeeds is satisfied.
13. Add tests for unavailable provenance, malformed timestamp, invalid dimensions, empty key fields, bad confidence score, bad RMSE, invalid accepted-view count and unknown policy/version is satisfied.
14. Ensure every invalid structural/provenance case returns an explicit non-reusable reason and cannot silently fall through to compatible is satisfied.
15. Still-valid original V01 behavior remains intact.
16. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
17. Previously accepted M02 children remain unregressed.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
20. PL-0066_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
