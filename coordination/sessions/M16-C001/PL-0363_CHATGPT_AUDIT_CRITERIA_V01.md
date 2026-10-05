# PL-0363 - ChatGPT Audit Criteria V01

Task: **Coordinated release numbering across Studio, Capture and PackScan**

All criteria mandatory.

1. Three version domains are read/validated independently.
2. Release train coordinates them without numerical lockstep.
3. Current source versions and commit provenance are explicit.
4. Version bump classification follows VERSIONING_POLICY.
5. No Git tag/GitHub Release is created.
6. Tests cover malformed/mismatched-but-valid independent versions and deterministic release identity.

7. No M17 implementation or PL-0368 release publication is pulled forward.
8. Implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0363_CODEX_PROMPT_V01.md
