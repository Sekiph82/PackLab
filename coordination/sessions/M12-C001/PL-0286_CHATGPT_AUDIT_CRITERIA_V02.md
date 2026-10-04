# PL-0286 - ChatGPT Audit Criteria V02

Task: **Implement front/back flexible-pack surfaces and seal zones with design-only authority**

All criteria are mandatory.

1. R02 tracker/master authorization, safe synchronization, M12 partial audit V02 and ADR-0005 were read.
2. Implementation is deterministic and limited to: Implement editable front/back surfaces and perimeter/seal zones for the PL-0285 flexible-pack family, preserving the exact explicit parent authority. Support planar or bounded simplified bulge representations as design geometry only. Stable artwork coordinates/features must survive edits. No measured-film-deformation implication.
3. Tests/evidence cover at minimum: front/back surfaces; seals; artwork coordinates; bounded bulge path; standalone authority persistence; scan-bound persistence if present; invalid crossing/negative seals; deterministic preview; design-only limitation.
4. CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY are explicit, discriminated and never faked or silently interchanged.
5. Existing scan-bound Design Model revision identity/serialization compatibility remains intact; standalone parents carry no fabricated scan-specific ancestry.
6. Scale/unit/deferred-validation authority is honest: no METRIC_VERIFIED, captured, physical, mold or manufacturing claim is invented.
7. No M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency/private evidence or later-scope implementation is introduced.
8. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; V02 log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0286_CODEX_PROMPT_V02.md
