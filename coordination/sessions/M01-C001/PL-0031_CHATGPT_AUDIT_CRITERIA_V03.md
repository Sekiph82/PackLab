# PL-0031 — ChatGPT Strict Remediation Audit Criteria V03

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_PROMPT_V03.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CHATGPT_AUDIT_V03.md

All **22 criteria** are mandatory.

1. Root TASKS.md authorized M01-REMEDIATION-BATCH-002 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 or unrelated future work was started.
5. No secret/private/confidential/signing/cache artifact was committed.
6. Changed files stay within the authorized V03 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is corrected, not merely described.
8. Do not change the working pytest behavior unless a new defect is found is satisfied.
9. Correct TESTING.md so it explicitly states strict unknown-marker validation is enabled by the --strict-markers addopt is satisfied.
10. Remove any claim that the canonical configuration sets strict_markers = true is satisfied.
11. Preserve unit/integration/slow registration, default not-slow behavior and explicit slow selection wording is satisfied.
12. Re-run the marker tests and full Python regression suite; record evidence without editing prior audit/log artifacts is satisfied.
13. Still-valid original and V02 behavior remains intact.
14. Focused regression evidence would fail on the audited pre-V03 defect.
15. Relevant accepted sibling M01 behavior remains unregressed.
16. git diff --check passes and builder TASKS.md diff is empty.
17. Protected-file/privacy/security review passes.
18. Platform evidence is truthful; unavailable native/device evidence is not fabricated.
19. V03 Codex log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0031_CODEX_LOG_V03.md and links the V03 prompt/criteria and blocking audit.
20. V03 log records start/implementation evidence, exact files, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
21. V03 log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
22. Actual GitHub source/diff/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently audits the actual V03 implementation/source/log. This task closes only if every criterion passes.
