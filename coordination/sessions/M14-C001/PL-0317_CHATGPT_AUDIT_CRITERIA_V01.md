# PL-0317 - ChatGPT Audit Criteria V01

Task: **Export label-dieline SVG with scale-verification marks**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Export deterministic vector SVG dielines from mm_unverified Label Zones with safe/bleed boundaries, explicit numerical units, verification marks, source provenance and physical-unverified disclaimer. RELATIVE zones must fail closed.
3. Tests/evidence cover at minimum: SVG parse; vector-only paths; mm dimensions/viewBox; safe/bleed layers; scale-verification marks with known numerical spacing; source revisions/digest; deterministic normalized output; RELATIVE rejection; no print-ready claim.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0317_CODEX_PROMPT_V01.md
