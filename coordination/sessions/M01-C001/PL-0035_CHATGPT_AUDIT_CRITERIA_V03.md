# PL-0035 — ChatGPT Strict Remediation Audit Criteria V03

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_PROMPT_V03.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CHATGPT_AUDIT_V02.md

All **23 criteria** are mandatory.

1. Root TASKS.md authorized M01-REMEDIATION-BATCH-002 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. Root TASKS.md was not edited by Codex.
4. No M02 or unrelated future work was started.
5. No secret/private/confidential/signing/cache artifact was committed.
6. Changed files stay within the authorized V03 scope plus only justified minimal adjacent files.
7. The exact blocking finding in the referenced audit is corrected, not merely described.
8. Keep the runner-owned Windows taskkill /PID <root> /T /F strategy unless a concrete defect requires a minimal change is satisfied.
9. Replace Windows os.kill(pid, 0) liveness checking with a non-destructive Windows process query. Do not add psutil or another dependency is satisfied.
10. Timeout and cancellation regressions must prove the parent and spawned child are already gone without the assertion itself terminating them is satisfied.
11. Add a negative/control proof showing the liveness helper detects a live process without killing it, and that the regression would fail for parent-only cleanup is satisfied.
12. Inspect taskkill completion. A nonzero/timeout/start failure must not be silently treated as successful tree cleanup; surface bounded structured cleanup error evidence while still attempting safe root cleanup is satisfied.
13. Preserve POSIX process-group behavior, shell=False, argument arrays, streaming callbacks and structured ProcessResult semantics is satisfied.
14. Still-valid original and V02 behavior remains intact.
15. Focused regression evidence would fail on the audited pre-V03 defect.
16. Relevant accepted sibling M01 behavior remains unregressed.
17. git diff --check passes and builder TASKS.md diff is empty.
18. Protected-file/privacy/security review passes.
19. Platform evidence is truthful; unavailable native/device evidence is not fabricated.
20. V03 Codex log exists at https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0035_CODEX_LOG_V03.md and links the V03 prompt/criteria and blocking audit.
21. V03 log records start/implementation evidence, exact files, defect mapping, validations, failures/fixes, regressions, scope/privacy, limitations and push evidence.
22. V03 log does not self-assign AUDITED_PASS or predeclare its future log commit SHA and ends AWAITING_AUDIT.
23. Actual GitHub source/diff/log are mutually consistent and no material task defect remains.

## Closure

ChatGPT independently audits the actual V03 implementation/source/log. This task closes only if every criterion passes.
