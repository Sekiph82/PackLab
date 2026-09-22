# PL-0057 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0057_CHATGPT_AUDIT_V01.md

All **21 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Encode the exact frozen DOS timestamp for 1980-01-01 00:00:00 in both local and central ZIP headers; do not write an all-zero DOS date is satisfied.
9. Make the Swift writer's DEFLATE implementation honor the accepted PackScan level-9 contract deterministically. Use an API/implementation that explicitly sets level 9; do not merely label an uncontrolled compression call as level 9 is satisfied.
10. Ensure the raw ZIP payload uses method 8 DEFLATE framing appropriate to ZIP rather than a zlib/gzip wrapper is satisfied.
11. Preserve deterministic entry order, no timestamp extra fields, CRC32, UTF-8 path bytes, path safety and partial-file safe finalization is satisfied.
12. Add byte-level regression evidence that parses the emitted local/central header fields and verifies DOS date/time, method, flags, CRC/size and absence of extra timestamp fields is satisfied.
13. If native Swift execution is unavailable on Windows, do not fabricate it. Add source/fixture evidence that is independently tied to the actual encoder implementation and leave native execution as a later macOS evidence boundary is satisfied.
14. Do not add personal signing/team/provisioning settings is satisfied.
15. Still-valid original V01 behavior remains intact.
16. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
17. Previously accepted M02 children remain unregressed.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
20. PL-0057_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
