# PL-0044 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0044_CHATGPT_AUDIT_V01.md

All **19 criteria** are mandatory.

1. TASKS.md authorized M02-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0051, later M02 child, or M03 work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Freeze one exact valid canonical ZIP central-directory timestamp for every deterministic PackScan entry. Use a representation that both Python and Swift can implement; 1980-01-01 00:00:00 is acceptable is satisfied.
9. Remove advisory language such as 'where the writer permits it'. Deterministic writers must apply the canonical value is satisfied.
10. Define the treatment of timestamp-related ZIP extra fields so they cannot reintroduce platform-dependent timestamps; either omit them or freeze their contents explicitly is satisfied.
11. Preserve the existing path, ordering, compression, authority and compatibility rules is satisfied.
12. Add a machine-level regression that loads layout.json and proves the timestamp rule is exact, required and standards-valid for the Python ZIP boundary is satisfied.
13. Still-valid original V01 behavior remains intact.
14. Focused tests are sensitivity-bearing and would fail on the pre-remediation defect.
15. Relevant accepted M00/M01 behavior remains unregressed.
16. git diff --check passes and builder TASKS.md diff is empty.
17. Platform/device/physical evidence boundaries are truthful.
18. PL-0044_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
