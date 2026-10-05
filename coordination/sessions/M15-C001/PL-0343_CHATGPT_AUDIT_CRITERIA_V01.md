# PL-0343 - ChatGPT Audit Criteria V01

Task: **Duplicate and variant relationship display**

All criteria are mandatory.

1. DUPLICATE and VARIANT relationship contracts exist with stable IDs and exact asset references.
2. Duplicate is symmetric; variant is directed and cycle/self-link safe.
3. Relationships are explicit/revisioned with provenance, not inferred automatically from similarity.
4. Related assets retain separate metadata/revision histories.
5. UI displays relationships and navigation deterministically.
6. Tests cover duplicate symmetry, variant chains/cycles, stale refs and display.

7. Scope remains inside PL-0343 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0343_CODEX_PROMPT_V01.md
