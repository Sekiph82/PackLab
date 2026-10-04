# PL-0323 - ChatGPT Audit Criteria V01

Task: **Persist material assignments per component**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 material-authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement project persistence/serialization for component-level geometry material, optional content appearance and PCR visual metadata using stable component IDs and exact Design Model revision provenance. Loading must fail closed on stale/deleted/ambiguous component references.
3. Tests/evidence cover at minimum: round-trip persistence; multiple components; replace/remove assignment; stale component rejection; deterministic normalized storage; exact model revision binding; migration/version field; privacy-safe data; source geometry immutability.
4. Exact Design Model/component provenance is preserved and all material/PBR/PCR values remain visual/design metadata unless explicit external certification authority is separately supplied.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0323_CODEX_PROMPT_V01.md
