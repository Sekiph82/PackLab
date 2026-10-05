# PL-0354 - ChatGPT Audit Criteria V01

Task: **macOS GitHub Actions Swift build and tests**

All criteria mandatory.

1. macOS workflow builds simulator target and runs unit tests with signing disabled.
2. Least-privilege, timeout and safe PR/push triggers.
3. Xcode/SDK/simulator facts are recorded without owner paths/secrets.
4. No signing secret is required for default CI.
5. Failure is nonzero and test failures cannot be masked.
6. Scope stays on existing Xcode project/tests.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0354_CODEX_PROMPT_V01.md
