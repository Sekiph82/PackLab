# PL-0367 - ChatGPT Audit Criteria V01

Task: **Rollback for incompatible Capture/Studio versions**

All criteria mandatory.

1. Rollback preserves original .packscan/raw evidence.
2. Uses release manifests/compatibility declarations, not version-number guessing.
3. Unsupported downgrade/migration paths fail/stop explicitly.
4. Covers Studio/Capture reinstall and build verification plus project/library backup considerations.
5. No private credentials/data in documentation.
6. Tests/validators cover representative compatibility matrix decisions where implemented.

7. No M17 implementation or PL-0368 release publication is pulled forward.
8. Implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0367_CODEX_PROMPT_V01.md
