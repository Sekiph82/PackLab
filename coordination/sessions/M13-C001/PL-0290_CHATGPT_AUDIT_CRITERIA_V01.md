# PL-0290 - ChatGPT Audit Criteria V01

Task: **Implement CAD capability adapter and version diagnostics**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement a PackLab-owned CAD/engineering adapter over the selected PL-0289 binding. Domain contracts must use PackLab-owned values and must not expose binding-owned classes. Adapter must probe observed binding version, observed OCCT/kernel version, platform/architecture, capability flags (BREP construction, revolve, loft, booleans, topology validation, tessellation, STEP read/write, STL write where supported) and unavailable/error states. No hidden install/download fallback. Provide deterministic conversions between PackLab profile/cross-section values and adapter input structures without claiming physical accuracy.
3. Tests/evidence cover at minimum: observed version/build/capability diagnostics; import unavailable path; PackLab-owned point/wire/shape handles or opaque IDs; no binding-type leakage; deterministic profile/cross-section conversion; capability failure; no runtime download; mm_unverified/relative authority preservation.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0290_CODEX_PROMPT_V01.md
