# PL-0360 - ChatGPT Audit Criteria V01

Task: **Prevent Apple signing material in public repo**

All criteria mandatory.

1. Guard covers certificate/profile/private-key/keychain material and secret-value patterns.
2. .gitignore/docs reinforce policy.
3. CI scan is content/path aware and redacts values.
4. False-positive escape requires explicit reviewed allowlist, not broad disable.
5. Existing public repo passes.
6. No real signing material is added as test fixture.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0360_CODEX_PROMPT_V01.md
