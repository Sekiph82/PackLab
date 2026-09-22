# PL-0049 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0049_CHATGPT_AUDIT_V01.md

All **22 criteria** are mandatory.

1. TASKS.md authorized M02-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0051, later M02 child, or M03 work was started.
5. No secret/private Kenya scan/confidential supplier/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Preserve the native CoreMotion monotonic timestamp in seconds since device boot for each motion sample is satisfied.
9. Define the photo/capture clock domain separately and record the mapping/anchor used to relate native monotonic motion time to UTC/photo time is satisfied.
10. Record mapping uncertainty/resolution and synchronization tolerance so no precision finer than evidence is implied is satisfied.
11. Record the selected CMAttitudeReferenceFrame as a frozen machine-readable value is satisfied.
12. Constrain available samples to contain the required motion payload and unavailable samples not to carry valid motion vectors is satisfied.
13. Keep stale and out_of_window states explicit and define how nearest/interpolated association uses the two-clock mapping is satisfied.
14. Add aligned/stale/missing fixtures/tests that exercise the native clock mapping, reference frame and contradictory state rejection is satisfied.
15. Preserve CoreMotion units and do not fabricate device execution is satisfied.
16. Still-valid original V01 behavior remains intact.
17. Focused tests are sensitivity-bearing and would fail on the pre-remediation defect.
18. Relevant accepted M00/M01 behavior remains unregressed.
19. git diff --check passes and builder TASKS.md diff is empty.
20. Platform/device/physical evidence boundaries are truthful.
21. PL-0049_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
22. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
