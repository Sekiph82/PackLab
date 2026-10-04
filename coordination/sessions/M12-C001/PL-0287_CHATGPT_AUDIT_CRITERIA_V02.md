# PL-0287 - ChatGPT Audit Criteria V02

Task: **Enforce flexible-pack visualization/design authority across reports and exports**

All criteria are mandatory.

1. R02 tracker/master authorization, safe synchronization, M12 partial audit V02 and ADR-0005 were read.
2. Implementation is deterministic and limited to: Implement guards so flexible-pack geometry remains visualization/design authority regardless of standalone or scan-bound parent. Prevent promotion to Scan Master, captured authority, mold/manufacturing authority, certified volume or physical tolerance. Reports/previews/export handoff must disclose parent authority and limitations consistently.
3. Tests/evidence cover at minimum: standalone and scan-bound guard paths; report/export authority propagation; Scan Master promotion rejection; mold/manufacturing/tolerance/certified-volume rejection; deterministic limitation metadata.
4. CAPTURED_SCAN_MASTER and STANDALONE_DESIGN_GEOMETRY are explicit, discriminated and never faked or silently interchanged.
5. Existing scan-bound Design Model revision identity/serialization compatibility remains intact; standalone parents carry no fabricated scan-specific ancestry.
6. Scale/unit/deferred-validation authority is honest: no METRIC_VERIFIED, captured, physical, mold or manufacturing claim is invented.
7. No M13 CAD/BREP/OpenCascade/STEP work, unreviewed dependency/private evidence or later-scope implementation is introduced.
8. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; V02 log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0287_CODEX_PROMPT_V02.md
