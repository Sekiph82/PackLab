# PL-0299 - ChatGPT Audit Criteria V01

Task: **Export OBJ and GLB from Design Model with stable part naming**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and physical-validation deferral were read.
2. Deterministic implementation is limited to: Implement deterministic OBJ and GLB export from M13 tessellated Design Model/assembly geometry with stable semantic part/component names and provenance. OBJ may remain in source model units with manifest-declared unit semantics. GLB may apply a documented coordinate-unit conversion required by the format/viewer, but that transform must be explicit, reversible in metadata and must not upgrade authority. Preserve component hierarchy where practical, stable names, material-free geometry identity, parent-authority mode and exact Design Model/CAD revisions. Do not use these exports as Scan Master or CAD/BREP truth.
3. Tests/evidence cover at minimum: single/multipart OBJ; GLB nodes/part names; deterministic geometry; explicit unit transform metadata; RELATIVE and mm_unverified handling; assembly hierarchy where supported; round-trip/basic parse; derived-export authority only.
4. Exact source authority/revisions and unit state are preserved; no RELATIVE->mm or unverified->physical/mold/manufacturing authority escalation occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log commits are separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0299_CODEX_PROMPT_V01.md
