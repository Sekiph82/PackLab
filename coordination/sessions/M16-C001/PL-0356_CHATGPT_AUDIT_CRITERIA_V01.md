# PL-0356 - ChatGPT Audit Criteria V01

Task: **Unsigned simulator build on every relevant change**

All criteria mandatory.

1. Relevant changes trigger unsigned simulator build.
2. Signing is explicitly disabled and no developer credentials are read.
3. Cross-language schema/fixture changes are included in triggers.
4. Simulator success is not mislabeled as device/signing acceptance.
5. Build products are provenance-labeled unsigned.
6. No secret-safe signed path is coupled to PR success.

7. No M17+ implementation, private data, secret leakage or unreviewed dependency.
8. Implementation/evidence and log publication are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0356_CODEX_PROMPT_V01.md
