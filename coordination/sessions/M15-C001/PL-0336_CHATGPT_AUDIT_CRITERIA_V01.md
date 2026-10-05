# PL-0336 - ChatGPT Audit Criteria V01

Task: **Link multiple POVU SKUs and artworks to one geometry**

All criteria are mandatory.

1. Multiple SKU records can reference one Packaging Asset geometry without duplicating geometry.
2. SKU links pin exact asset and optional model/artwork/assignment revision IDs.
3. Artwork remains separate presentation authority; no artwork bytes embedded in SKU metadata.
4. Stale/malformed/duplicate SKU references fail closed.
5. Historical revisions remain immutable and deterministic.
6. Tests prove two+ SKUs can share geometry while retaining distinct artwork/provenance.

7. Scope remains inside PL-0336 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0336_CODEX_PROMPT_V01.md
