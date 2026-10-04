# PL-0285 - ChatGPT Audit Criteria V02

Task: **Define simplified sachet/pouch Design Model with standalone design authority**

All criteria are mandatory.

1. R02 tracker/master authorization, safe synchronization, M12 partial audit V02 and ADR-0005 were read.
2. Implementation is deterministic and limited to: Define a simplified sachet/pouch parametric family focused on artwork surfaces, overall dimensions, seal zones and basic front/back shape. Model-only creation must use STANDALONE_DESIGN_GEOMETRY by default. If a scan-bound path is supported, it must remain explicitly CAPTURED_SCAN_MASTER and separate. Classify the family as visualization/design geometry rather than mold-grade captured surface authority.
3. Tests/evidence cover at minimum: standalone rectangular pouch/sachet; optional explicit scan-bound path if implemented; overall dimensions; seal-zone parameters; stable artwork surfaces; invalid seal/dimension relationships; deterministic graph/serialization/preview; visualization-only authority flag; no fake scan ancestry.
4. CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY are explicit, discriminated and never faked or silently interchanged.
5. Existing scan-bound Design Model revision identity/serialization compatibility remains intact; standalone parents carry no fabricated scan-specific ancestry.
6. Scale/unit/deferred-validation authority is honest: no METRIC_VERIFIED, captured, physical, mold or manufacturing claim is invented.
7. No M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency/private evidence or later-scope implementation is introduced.
8. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; V02 log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0285_CODEX_PROMPT_V02.md
