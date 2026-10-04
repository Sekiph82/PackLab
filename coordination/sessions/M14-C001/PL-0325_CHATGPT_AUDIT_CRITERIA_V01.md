# PL-0325 - ChatGPT Audit Criteria V01

Task: **Create deterministic Blender scene-generation script from PackLab project data**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement a deterministic scene-package generator that converts exact accepted PackLab model/export, Label Zone/artwork and material-assignment revisions into a bounded Blender Python/JSON input package. The generated package must use relative/project-contained asset references and must not execute arbitrary user code.
3. Tests/evidence cover at minimum: deterministic script/manifest; exact source digests/revisions; safe relative asset references; escaping/quoting; bounded object/material/artwork counts; no arbitrary code injection; no ambient path identity; versioned scene contract; no source mutation.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0325_CODEX_PROMPT_V01.md
