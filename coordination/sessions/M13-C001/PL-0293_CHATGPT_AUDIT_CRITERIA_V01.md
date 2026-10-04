# PL-0293 - ChatGPT Audit Criteria V01

Task: **Implement boolean feature support for handle openings and simple indentations**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement a narrow, deterministic boolean feature layer needed by existing parametric handle openings and simple grip/indent features. Boolean operations must be driven by explicit Design Model feature parameters/reference geometry, not raw scan triangles. Record operation type, tool/body feature IDs, adapter/kernel result, topology status and failure diagnostics. Limit scope to subtraction/cut operations required by current M12 features; no arbitrary CAD modeling suite. Boolean failure must remain explicit and must not silently drop the feature.
3. Tests/evidence cover at minimum: handle opening cut; simple indent cut where representable; tool outside body; nonintersecting boolean; invalid tool; deterministic operation provenance; stable feature linkage; failure leaves parent BREP/model unchanged; no raw scan boolean.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0293_CODEX_PROMPT_V01.md
