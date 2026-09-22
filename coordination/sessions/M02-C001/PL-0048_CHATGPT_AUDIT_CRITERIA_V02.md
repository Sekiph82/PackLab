# PL-0048 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0048_CHATGPT_AUDIT_V01.md

All **22 criteria** are mandatory.

1. TASKS.md authorized M02-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0051, later M02 child, or M03 work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Freeze the exact ARKit camera/world to PackScan basis conversion, including source/destination axis directions, handedness, viewing direction and matrix multiplication/order convention is satisfied.
9. Account explicitly for ARKit camera viewing along negative Z versus PackScan stored +Z-forward convention; a column-major/row-major memory-layout conversion alone is insufficient is satisfied.
10. Freeze translation units explicitly as metres or another single named canonical unit is satisfied.
11. Require coordinate_convention for stored available/degraded poses is satisfied.
12. Constrain valid status/tracking_state combinations so contradictory combinations are rejected is satisfied.
13. Define quaternion conversion consistently with the same basis change and preserve xyzw ordering is satisfied.
14. Add deterministic synthetic basis-vector/pose tests and negative fixtures for contradictory tracking states is satisfied.
15. Preserve no-LiDAR assumptions and do not claim native ARKit execution on Windows is satisfied.
16. Still-valid original V01 behavior remains intact.
17. Focused tests are sensitivity-bearing and would fail on the pre-remediation defect.
18. Relevant accepted M00/M01 behavior remains unregressed.
19. git diff --check passes and builder TASKS.md diff is empty.
20. Platform/device/physical evidence boundaries are truthful.
21. PL-0048_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
22. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
