# PL-0048 — ChatGPT Strict Remediation Audit Criteria V03

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V03.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_V02.md

All **24 criteria** are mandatory.

1. TASKS.md authorized M02-REMEDIATION-BATCH-002 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0051, later M02 child, or M03 work was started.
5. No private/confidential/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V03 scope plus only justified minimal adjacent files.
7. The V02 handedness finding is corrected, not renamed or obscured.
8. PackScan pose space is truthfully right-handed.
9. PackScan stores X right, Y up, +Z out of the screen/device side, with camera viewing direction -Z.
10. The old single-axis reflection is removed from the canonical ARKit-to-PackScan conversion.
11. Mathematical ARKit-to-PackScan pose conversion is identity for the shared right-handed basis.
12. Row-major JSON versus Apple's matrix storage is documented as serialization/layout, not a geometric reflection.
13. Translation unit remains metres.
14. Quaternion order remains xyzw and the component mapping is mathematically consistent with the shared basis.
15. Coordinate-convention and basis-conversion identifiers are required by schema.
16. available -> normal is enforced.
17. degraded -> limited is enforced.
18. unavailable -> not_available plus null confidence and no transforms/quaternion is enforced.
19. A negative unavailable/normal fixture is rejected by actual Draft 2020-12 validation.
20. Sensitivity tests prove right-handedness and -Z camera-forward semantics and reject the old reflected +Z-forward convention.
21. Still-valid timestamp, provenance and no-LiDAR boundaries remain intact.
22. Full relevant regression/quality checks are green and TASKS.md diff is empty.
23. PL-0048_CODEX_LOG_V03.md accurately records actual GitHub evidence and ends READY_FOR_INDEPENDENT_AUDIT.
24. Source, tests, fixtures, docs and log are mutually consistent and no material PL-0048 defect remains.

## Closure

ChatGPT independently audits the V03 implementation. PL-0048 closes only if every criterion passes.
