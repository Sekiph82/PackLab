# PL-0361 - ChatGPT Audit Criteria V01

Task: **Publish signed/unsigned artifacts with provenance**

All criteria mandatory.

1. Every iOS artifact has machine-readable provenance with signing state.
2. Artifact digest/length validated before upload.
3. Names distinguish simulator/unsigned archive/signed IPA.
4. Sidecar excludes secrets, keychain paths and profile/cert bytes.
5. Version/build/schema/commit/Xcode facts included.
6. Retention and least-privilege policies preserved.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0361_CODEX_PROMPT_V01.md
