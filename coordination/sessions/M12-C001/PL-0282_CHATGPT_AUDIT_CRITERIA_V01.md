# PL-0282 - ChatGPT Audit Criteria V01

Task: **Export assembly hierarchy metadata for component-capable formats**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement backend-neutral assembly export-handoff metadata preserving component hierarchy, revision IDs, placements, units, provenance and library-component references for future component-capable exporters. Do not implement M13 CAD/STEP hierarchy export. Existing preview/GLB-compatible metadata may be produced only if it remains explicitly non-CAD and deferred-accuracy.
3. Tests/evidence cover at minimum: hierarchy ordering, component transforms/revisions, library provenance, stale/missing component rejection, deterministic manifest, mm_unverified/deferred disclaimer, no STEP/CAD export.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0282_CODEX_PROMPT_V01.md
