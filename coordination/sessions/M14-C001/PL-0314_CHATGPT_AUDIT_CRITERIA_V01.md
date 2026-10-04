# PL-0314 - ChatGPT Audit Criteria V01

Task: **Add safe-margin/bleed metadata**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Add non-destructive safe-margin and bleed metadata to label dielines with explicit numerical-mm semantics only on the mm_unverified dieline path. These values are user/design intent, not printer/manufacturer certification.
3. Tests/evidence cover at minimum: zero/positive values; invalid/negative/non-finite rejection; inner safe boundary and outer bleed boundary; deterministic metadata; source dieline identity; disclaimer; no geometry-source mutation.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0314_CODEX_PROMPT_V01.md
