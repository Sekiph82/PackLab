# PL-0316 - ChatGPT Audit Criteria V01

Task: **Support front/back artwork variants and wrap labels**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement deterministic artwork-assignment variants for front, back, and wrap zones, including explicit variant IDs and wrap seam/orientation metadata. Assignments remain reversible presentation state.
3. Tests/evidence cover at minimum: front/back independent variants; wrap seam/orientation; missing/wrong zone kind rejection; deterministic assignment identity; replacement/removal; exact zone/artwork revision binding; no source geometry mutation.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0316_CODEX_PROMPT_V01.md
