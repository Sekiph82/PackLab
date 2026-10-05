# PL-0359 - ChatGPT Audit Criteria V01

Task: **Free-first unsigned fallback and installation route**

All criteria mandatory.

1. Unsigned fallback artifact remains available without credentials.
2. Documentation clearly distinguishes simulator, unsigned archive and physically installable signed IPA.
3. Physical iPhone route requires valid signing/provisioning.
4. Any Windows community-tool route is optional, not bundled/endorsed as official, and includes credential/privacy caveats.
5. No secrets or private Apple account data enter repo.
6. No false installation claim for unsigned artifacts.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0359_CODEX_PROMPT_V01.md
