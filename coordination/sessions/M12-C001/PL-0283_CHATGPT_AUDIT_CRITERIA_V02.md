# PL-0283 - ChatGPT Audit Criteria V02

Task: **Define tube parametric family with explicit standalone Design Geometry root**

All criteria are mandatory.

1. R02 tracker/master authorization, safe synchronization, M12 partial audit V02 and ADR-0005 were read.
2. Implementation is deterministic and limited to: First implement the ADR-0005 authority foundation required for truthful model-only Design Models, then define the tube family.

Authority foundation may modify shared Design Model parent/binding/serialization/history/validation/preview contracts as necessary, but must be backward compatible for existing scan-bound revisions. Introduce an immutable versioned standalone Design Geometry root and explicit parent discrimination. No fake scan lineage is allowed.

Then define the collapsible/squeeze tube family with body, shoulder, neck, cap and crimp stable features and backend-neutral parametric operations. Support:
(a) scan-bound tube Design Models using the existing exact Scan Master parent path; and
(b) model-only tube creation from an explicit standalone Design Geometry root.
Do not claim flexible-wall physical deformation accuracy.
3. Tests/evidence cover at minimum: standalone root deterministic identity/digest/provenance; no fake scan fields; scan-bound revision/serialization regression stability; standalone serialization/history/validation/preview; captured-only service rejection of standalone; tube graph for both parent modes; body/shoulder/neck/cap/crimp stable features; impossible dimensions; RELATIVE/mm_unverified semantics; deterministic preview.
4. CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY are explicit, discriminated and never faked or silently interchanged.
5. Existing scan-bound Design Model revision identity/serialization compatibility remains intact; standalone parents carry no fabricated scan-specific ancestry.
6. Scale/unit/deferred-validation authority is honest: no METRIC_VERIFIED, captured, physical, mold or manufacturing claim is invented.
7. No M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency/private evidence or later-scope implementation is introduced.
8. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; V02 log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0283_CODEX_PROMPT_V02.md
