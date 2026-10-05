# PL-0364 - ChatGPT Audit Criteria V01

Task: **Release manifest with dependencies and compatibility**

All criteria mandatory.

1. Manifest binds exact semantic versions, commit, artifact provenance and dependency/build identities.
2. Declares PackScan read/write/migration compatibility per policy.
3. Includes signing state and third-party notice/inventory references.
4. Missing required provenance/compliance data fails closed.
5. Canonical manifest identity is path/timestamp independent where appropriate.
6. No M17 acceptance/release publication claim.

7. No M17 implementation or PL-0368 release publication is pulled forward.
8. Implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0364_CODEX_PROMPT_V01.md
