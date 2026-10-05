# PL-0332 - ChatGPT Audit Criteria V01

Task: **Define Packaging Asset schema**

All criteria are mandatory.

1. Immutable deterministic Packaging Asset contract exists with all required fields and stable internal ID.
2. Numeric volume/weight/dimensional fields are finite, bounded and unit-explicit; unknown is distinct from zero.
3. Package family/material/closure/status inputs are bounded and validated without implying certification.
4. Deterministic serialization/revision identity is path/machine independent.
5. No geometry/artwork bytes, project root, external path, network or physical/manufacturing claim is embedded.
6. Tests cover valid families, unknowns, invalid IDs/units/nonfinite values, deterministic identity and serialization.

7. Scope remains inside PL-0332 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0332_CODEX_PROMPT_V01.md
