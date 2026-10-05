# PL-0358 - ChatGPT Audit Criteria V01

Task: **Optional secret-safe signed IPA path**

All criteria mandatory.

1. Signed job is conditional/protected and absent credentials cause SKIP, not fake success.
2. Fork/PR contexts cannot receive signing secrets.
3. Temporary keychain/cert/profile lifecycle is ephemeral with always-cleanup.
4. Secret values never appear in workflow source/log commands/artifacts.
5. Exported IPA is validated and provenance-labeled SIGNED.
6. No signing material is committed/uploaded.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0358_CODEX_PROMPT_V01.md
