# PL-0043 — ChatGPT Strict Remediation Audit Criteria V04

Repository: https://github.com/Sekiph82/PackLab
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CODEX_PROMPT_V04.md
Blocking audit: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M01-C001/PL-0043_CHATGPT_AUDIT_V03.md

All **22 criteria** are mandatory.

1. TASKS.md authorized M01-REMEDIATION-BATCH-003 / CODEX before material work.
2. Repository synchronization was safe and no destructive Git operation was used.
3. TASKS.md was not edited by Codex.
4. No M02 or unrelated future work was started.
5. No secret/private/confidential/signing/cache artifact was committed.
6. Changed files stay within the authorized V04 scope plus only justified minimal adjacent files.
7. The correct Xcode project graph itself was not rewritten merely to manufacture a diff.
8. Existing ENABLE_TESTABILITY, BUNDLE_LOADER, TEST_HOST and no-personal-signing checks remain intact.
9. The static guard proves PackLabCaptureTests.swift membership specifically inside the Test Sources PBXSourcesBuildPhase.
10. The static guard proves the PackLabCapture dependency specifically inside the PackLabCaptureTests PBXNativeTarget dependencies block.
11. Standalone PBXBuildFile object presence alone cannot satisfy the source-membership assertion.
12. Standalone PBXTargetDependency object presence alone cannot satisfy the target-dependency assertion.
13. Focused mutation/helper evidence removes only the Test Sources membership while leaving the standalone build-file object and proves the guard fails.
14. Focused mutation/helper evidence removes only the test-target dependency membership while leaving the standalone dependency object and proves the guard fails.
15. The durable regression remains Xcode-free and suitable for the normal Windows/Linux pytest suite.
16. Accepted PL-0043 V02/V03 wiring and all relevant sibling M01 behavior remain unregressed.
17. Full relevant Python regression, Ruff and mypy evidence is green.
18. git diff --check passes and builder TASKS.md diff is empty.
19. Platform evidence is truthful and no unavailable native/device execution is fabricated.
20. PL-0043_CODEX_LOG_V04.md exists, links prompt/criteria/blocking audit, records exact evidence and ends AWAITING_AUDIT without self-PASS or future log SHA.
21. Actual GitHub source, diff and log claims are mutually consistent.
22. No material PL-0043 defect remains within M01 frozen scope.

## Closure

ChatGPT independently audits the actual V04 source/diff/log. PL-0043 closes only if every criterion passes.
