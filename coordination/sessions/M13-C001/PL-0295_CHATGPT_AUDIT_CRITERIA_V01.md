# PL-0295 - ChatGPT Audit Criteria V01

Task: **Preserve named feature references across CAD regeneration where practical**

All criteria are mandatory.

1. M13 tracker/master authorization, safe synchronization, M12 AUDITED_PASS, ADR-0005 and M09 deferral were read.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement a PackLab-owned named-feature mapping layer between stable Design Model feature IDs and regenerated CAD subshape references. Because OCCT topological naming can change across regeneration, never claim universal stable native subshape IDs. Preserve references where deterministic matching is supported by explicit operation/feature lineage; otherwise emit unresolved/ambiguous mapping diagnostics rather than silently retargeting. Mapping must survive ordinary parameter regeneration cases covered by tests and retain exact Design Model/CAD representation revisions.
3. Tests/evidence cover at minimum: body/neck/cap/handle feature mapping; ordinary parameter regeneration; boolean-result lineage; ambiguous topology-change case; unresolved mapping explicit; no preview-index/native-hash authority; deterministic mapping evidence.
4. CAD/BREP remains derived from exact Design Model revision; parent authority, units and DEFERRED_OWNER_VALIDATION remain explicit; no RELATIVE->mm or unverified->physical/mold authority promotion occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced. PL-0289 alone owns dependency/lock/license selection.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0295_CODEX_PROMPT_V01.md
