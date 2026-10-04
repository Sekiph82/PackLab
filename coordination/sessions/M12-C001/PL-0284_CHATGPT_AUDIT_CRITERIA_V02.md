# PL-0284 - ChatGPT Audit Criteria V02

Task: **Implement tube fitting from scan/reference dimensions under explicit authority provenance**

All criteria are mandatory.

1. R02 tracker/master authorization, safe synchronization, M12 partial audit V02 and ADR-0005 were read.
2. Implementation is deterministic and limited to: Fit the tube family from either:
(a) exact Scan Master evidence, producing/retaining a CAPTURED_SCAN_MASTER parent; or
(b) explicitly supplied reference/user dimensions under STANDALONE_DESIGN_GEOMETRY authority.
For mixed evidence, keep captured measurements, reference dimensions and modeled parameters separately labeled and choose the parent authority explicitly. Never silently convert reference dimensions into captured evidence. Missing flexible-wall regions remain uncertain; do not infer hidden wall thickness/material deformation.
3. Tests/evidence cover at minimum: scan-bound fit; standalone reference-dimension fit; mixed source provenance; explicit parent authority selection; no fake scan lineage; contradictory/missing evidence; mm_unverified semantics; captured-only comparison rejection for standalone; no wall thickness/material deformation inference.
4. CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY are explicit, discriminated and never faked or silently interchanged.
5. Existing scan-bound Design Model revision identity/serialization compatibility remains intact; standalone parents carry no fabricated scan-specific ancestry.
6. Scale/unit/deferred-validation authority is honest: no METRIC_VERIFIED, captured, physical, mold or manufacturing claim is invented.
7. No M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency/private evidence or later-scope implementation is introduced.
8. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; V02 log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CODEX_PROMPT_V02.md
