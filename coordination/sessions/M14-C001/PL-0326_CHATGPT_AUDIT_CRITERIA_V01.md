# PL-0326 - ChatGPT Audit Criteria V01

Task: **Import Design Model, materials and artwork into render scene**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Using the accepted scene package and real Blender headless capability, implement scene construction that imports the derived Design Model mesh/GLB, applies component material assignments and maps artwork to Label Zones non-destructively. Fail closed on source digest/revision mismatch.
3. Tests/evidence cover at minimum: real headless smoke; model import; stable component/part mapping; material assignment; front/back/wrap artwork mapping; missing/stale asset rejection; RELATIVE/mm_unverified metadata preservation; no geometry-authority mutation; no external network access.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0326_CODEX_PROMPT_V01.md
