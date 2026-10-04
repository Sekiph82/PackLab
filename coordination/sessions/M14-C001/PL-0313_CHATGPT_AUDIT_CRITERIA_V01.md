# PL-0313 - ChatGPT Audit Criteria V01

Task: **Generate 2D label boundary/dieline in millimetres**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Generate a deterministic 2D label boundary/dieline from an accepted Label Zone only when the source is METRIC_UNVERIFIED/mm_unverified. RELATIVE sources must fail closed. Numerical millimetres remain physically unverified.
3. Tests/evidence cover at minimum: front/back/wrap boundary; 2D coordinate frame and winding; known dimensions; repeatability; RELATIVE rejection; mm_unverified disclaimer; no physical/print-fit claim; source zone/model/CAD revision binding.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0313_CODEX_PROMPT_V01.md
