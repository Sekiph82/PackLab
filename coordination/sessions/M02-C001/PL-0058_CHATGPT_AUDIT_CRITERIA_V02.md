# PL-0058 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0058_CHATGPT_AUDIT_V01.md

All **21 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Build the PL-0058 proof on the corrected PL-0057 writer; do not use the Python writer to manufacture the positive 'Swift output' package under test is satisfied.
9. Provide deterministic Swift-side package bytes or an independently derived byte-level Swift encoder fixture whose provenance is explicitly tied to the corrected Swift implementation is satisfied.
10. If no authorized macOS/Xcode execution exists, label the evidence honestly as source-derived/static and do not call it native Swift-produced execution evidence is satisfied.
11. Make Python read/validate those Swift-side bytes through the real PackScan validator is satisfied.
12. Verify schema/layout/checksum/photo metadata compatibility, not just hard-coded source strings is satisfied.
13. Add a negative mutation to the Swift-side package bytes that leaves the rest of the package intact and prove Python rejects it is satisfied.
14. Record fixture provenance: Swift source commit, contract/schema version, generation method and native-vs-static evidence level is satisfied.
15. Still-valid original V01 behavior remains intact.
16. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
17. Previously accepted M02 children remain unregressed.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
20. PL-0058_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
21. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
