# PL-0060 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0060_CHATGPT_AUDIT_V01.md

All **21 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Keep the existing A4/A3 SVG source geometry unless a real geometry defect is found is satisfied.
9. Strengthen tests to parse actual SVG geometry rather than trusting duplicated data-* metadata is satisfied.
10. Verify root width/height/viewBox correspond to exact A4/A3 millimetre page geometry is satisfied.
11. Derive marker bounds/centres from the marker geometry and prove the encoded marker side is 40 mm and the declared centre-to-centre distances are correct is satisfied.
12. Verify the actual 100 mm reference bar geometry from SVG elements is satisfied.
13. Add mutation/helper evidence where SVG geometry changes but data-* metadata remains unchanged and prove the guard fails is satisfied.
14. Preserve print-at-100%, no-fit/no-scale and no-physical-accuracy-claim boundaries is satisfied.
15. Still-valid original V01 behavior remains intact.
16. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
17. Previously accepted M02 children remain unregressed.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
20. PL-0060_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
