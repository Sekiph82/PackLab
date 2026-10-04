# PL-0292 - ChatGPT Audit Criteria V01

Task: **Convert lofted cross-section Design Models into BREP solids**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic BREP generation for accepted loft-based Design Models from ordered editable cross-sections. Preserve section order, symmetry/asymmetry, stable feature references and exact model revision/parent authority. Validate section closure, compatible topology/order, nonzero area and loft failure diagnostics. Output remains a derived CAD representation linked to Design Model truth. Do not silently heal unsupported gaps beyond explicitly documented OCCT operations.
3. Tests/evidence cover at minimum: elliptical/rounded jerrycan loft; asymmetric section set; ordered sections; mismatched/degenerate section rejection; deterministic representation identity; scan-bound/standalone propagation; no hidden healing/manufacturing claim.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0292_CODEX_PROMPT_V01.md
