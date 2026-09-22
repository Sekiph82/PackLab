# PL-0056 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0056_CHATGPT_AUDIT_V01.md

All **21 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Make the committed PackScan Draft 2020-12 schemas the canonical validation source used by the Python reader/validator rather than manually duplicating only a subset of field rules is satisfied.
9. Validate manifest.json with the actual manifest schema and checksum/control JSON with their actual schemas before semantic/container checks is satisfied.
10. Resolve local schema references deterministically from repository/package-owned schema resources without network access is satisfied.
11. Map schema validation failures into stable PackScanError codes/details without weakening the schema semantics is satisfied.
12. Preserve ZIP path, duplicate, checksum, size, truncation, authority and extraction-safety checks from PL-0054 is satisfied.
13. Add regressions proving validate_packscan rejects values the canonical schema rejects, including empty device model, malformed os_version and invalid optional manifest fields is satisfied.
14. Avoid creating a second hand-written schema truth. If semantic cross-record rules are needed, keep them clearly separate from JSON-Schema validation is satisfied.
15. Still-valid original V01 behavior remains intact.
16. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
17. Previously accepted M02 children remain unregressed.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
20. PL-0056_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
