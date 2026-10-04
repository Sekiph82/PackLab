# PL-0310 - ChatGPT Audit Criteria V01

Task: **Define Label Zone entity independent of artwork image**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement an immutable, deterministic Label Zone domain contract bound to exact Design Model/CAD authority and stable component/feature references. A zone must represent geometric placement/boundary intent only, with no artwork bytes or image dependency.
3. Tests/evidence cover at minimum: front/back/wrap zone kinds; stable zone identity; exact source model/BREP/parent/unit provenance; finite bounded placement parameters; stale/deleted feature rejection; deterministic serialization; proof that changing artwork or having no artwork cannot change zone identity.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0310_CODEX_PROMPT_V01.md
