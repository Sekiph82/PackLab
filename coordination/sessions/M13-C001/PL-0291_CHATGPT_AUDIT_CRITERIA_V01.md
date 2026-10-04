# PL-0291 - ChatGPT Audit Criteria V01

Task: **Convert profile/revolve Design Models into BREP solids**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement deterministic conversion of accepted M11/M12 revolve-based Design Models into BREP solids through the PackLab CAD adapter. Consume explicit profile/revolve operation, stable feature references, exact model revision and parent-authority metadata. Validate profile closure/axis/orientation and reject invalid/self-intersecting/degenerate inputs. Output is a new CAD representation revision linked to the exact Design Model, never a replacement for Design Model or Scan Master. Coordinates remain in the Design Model's coordinate unit; do not silently treat RELATIVE as mm. For mm_unverified models, the CAD representation may carry millimetre-like numerical units only with explicit unverified authority metadata.
3. Tests/evidence cover at minimum: cylinder/bottle revolve; axis/profile validation; deterministic BREP digest/revision; scan-bound and standalone parent propagation; RELATIVE vs mm_unverified units; degenerate/self-intersecting profile rejection; Design Model immutability; no physical/mold claim.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CODEX_PROMPT_V01.md
