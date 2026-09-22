# PL-0062 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0062_CHATGPT_AUDIT_V01.md

All **20 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Make the PL-0059 machine-readable marker policy the canonical source used by the detector for dictionary/family selection, directly or through one generated/shared PackLab policy loader is satisfied.
9. Eliminate an independently hard-coded detector dictionary truth that can drift from calibration-marker-policy.json is satisfied.
10. Fail clearly if the policy dictionary cannot be mapped to an available OpenCV aruco dictionary rather than silently substituting another family is satisfied.
11. Add a regression that mutates or substitutes policy dictionary data and proves detector resolution follows/rejects the policy rather than an embedded constant is satisfied.
12. Strengthen duplicate-marker-ID testing through injected/helper-level detector results so duplicate IDs deterministically produce the bounded duplicate_marker_id invalid outcome is satisfied.
13. Preserve deterministic corner ordering/refinement, malformed-image handling and detection-only scope with no physical scale inference is satisfied.
14. Still-valid original V01 behavior remains intact.
15. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
16. Previously accepted M02 children remain unregressed.
17. git diff --check passes and builder TASKS.md diff is empty.
18. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
19. PL-0062_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
20. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
