# PL-0340 - ChatGPT Audit Criteria V01

Task: **Search by ID, name, supplier and family**

All criteria are mandatory.

1. Search covers exact requested fields: ID, name, supplier, package family.
2. Casefold/normalization and bounded query handling are deterministic.
3. Empty query returns stable unfiltered order; combined-field matches do not duplicate assets.
4. Search does not inspect attachment bytes or use network/external index.
5. UI search updates browser results without mutating library state.
6. Tests cover Unicode/case/partial/exact/empty queries and stable ordering.

7. Scope remains inside PL-0340 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0340_CODEX_PROMPT_V01.md
