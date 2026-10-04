# PL-0330 - ChatGPT Audit Criteria V01

Task: **Export GLB with materials/textures for lightweight viewing**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement real Blender headless GLB export for lightweight viewing with accepted visual materials and mapped artwork/textures. Preserve stable semantic part/component names and include a PackLab sidecar manifest with exact source/render/material/artwork revisions, transforms and output digest.
3. Tests/evidence cover at minimum: valid glTF/GLB parse; materials/textures present where assigned; stable part names; source/parent/unit metadata sidecar; texture/image references embedded or project-safe per contract; no external URI/network; RELATIVE/mm_unverified authority preserved; no manufacturing claim.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0330_CODEX_PROMPT_V01.md
