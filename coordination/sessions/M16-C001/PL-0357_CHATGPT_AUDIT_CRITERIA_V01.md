# PL-0357 - ChatGPT Audit Criteria V01

Task: **Unsigned device archive job**

All criteria mandatory.

1. Device/generic iOS archive builds without signing secrets.
2. Artifact provenance labels it UNSIGNED and records version/build/commit/Xcode.
3. No fake/supposed installable IPA is produced without signing/export authority.
4. Public artifact excludes keychain/profile/certificate/private data.
5. Artifact retention follows PL-0352 policy.
6. Archive job is independently green without PL-0358 credentials.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0357_CODEX_PROMPT_V01.md
