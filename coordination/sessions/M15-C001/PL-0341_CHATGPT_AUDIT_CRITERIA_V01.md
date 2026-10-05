# PL-0341 - ChatGPT Audit Criteria V01

Task: **Filters for volume, material, closure and status**

All criteria are mandatory.

1. Filters cover volume, material, closure and status and compose with search.
2. Volume handling is unit-explicit and unknown != zero.
3. Multi-filter semantics are deterministic and documented/tested.
4. Provenance distinctions are retained in returned records; filtering does not promote estimates to facts.
5. Clear/reset restores search-only/unfiltered state predictably.
6. Headless UI/service tests cover combinations, unknowns, boundaries and stable order.

7. Scope remains inside PL-0341 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0341_CODEX_PROMPT_V01.md
