# PL-0311 - ChatGPT Audit Criteria V01

Task: **Implement manual front/back/wrap Label Zone placement on Design Model**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement manual placement/edit operations for front, back, and wrap Label Zones on exact Design Model/CAD sources without altering source geometry. Placement must use canonical coordinate frames and explicit stable references.
3. Tests/evidence cover at minimum: front/back/wrap placement; canonical frame/orientation; deterministic revisioning; bounds/surface validation; invalid/non-finite/out-of-surface rejection; source immutability; scan-bound and standalone parents; RELATIVE/mm_unverified preservation.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0311_CODEX_PROMPT_V01.md
