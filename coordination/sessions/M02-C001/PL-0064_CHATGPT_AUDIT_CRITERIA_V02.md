# PL-0064 — ChatGPT Strict Remediation Audit Criteria V02

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CODEX_PROMPT_V02.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M02-C001/PL-0064_CHATGPT_AUDIT_V01.md

All **19 criteria** are mandatory.

1. TASKS.md authorized M02-RESUME-REMEDIATION-BATCH-001 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md and ChatGPT audit artifacts were not edited by Codex.
4. No PL-0067, PL-0068 or M03 work was started.
5. No private scan/confidential supplier/credential/signing/cache artifact entered public Git.
6. Changed files stay within the authorized V02 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced V01 audit is corrected rather than merely documented.
8. Choose and freeze one semantics for residual/spread thresholds: either true hard consistency gates or score-normalization reference values is satisfied.
9. If they are hard maxima, fail closed above them. If they are scoring reference values, rename constants/docs so 'MAX'/'gate' language does not imply hard rejection is satisfied.
10. Add immediate below/exact/above boundary tests for residual 0.05, edge spread 0.03, marker-count full-credit 4, accepted score 0.80 and warning score 0.60 is satisfied.
11. Add adversarial tests where one metric is beyond its frozen boundary while the other factors are strong, proving the chosen semantics is satisfied.
12. Preserve deterministic accepted/warning/rejected outputs and the explicit provisional/non-physical-accuracy status is satisfied.
13. Still-valid original V01 behavior remains intact.
14. Focused tests are sensitivity-bearing and fail on the pre-remediation defect.
15. Previously accepted M02 children remain unregressed.
16. git diff --check passes and builder TASKS.md diff is empty.
17. Platform/device/physical evidence boundaries are truthful and unavailable evidence is not fabricated.
18. PL-0064_CODEX_LOG_V02.md exists, links prompt/criteria/audit, records actual implementation/evidence and ends READY_FOR_INDEPENDENT_AUDIT.
19. Actual GitHub source/diff/tests/log are mutually consistent and no material child defect remains.

## Closure

ChatGPT independently audits the actual V02 GitHub state. This child closes only if every criterion passes.
