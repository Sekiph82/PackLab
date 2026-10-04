# PL-0312 - ChatGPT Audit Criteria V01

Task: **Implement curvature/slope analysis to suggest label-safe regions**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement bounded deterministic CAD-derived surface curvature/slope analysis that produces advisory label-safe candidate regions. Suggestions are evidence only and never automatic production approval.
3. Tests/evidence cover at minimum: known cylinder/flat/sloped/curved fixtures; threshold boundaries; deterministic ranking; feature/component provenance; bounded sampling; no pixel/mesh-index authority; explicit advisory limitation; RELATIVE and mm_unverified behavior.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0312_CODEX_PROMPT_V01.md
