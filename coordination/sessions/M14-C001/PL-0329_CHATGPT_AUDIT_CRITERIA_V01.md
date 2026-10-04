# PL-0329 - ChatGPT Audit Criteria V01

Task: **Render front/three-quarter/back standard views**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement ordered headless rendering of standard front, three-quarter and back views using the accepted camera presets, with one manifest tying all outputs to the exact same scene/source revisions and render settings.
3. Tests/evidence cover at minimum: three required views; unique camera IDs/transforms; non-empty/non-clipped renders; consistent dimensions/settings; per-output digests; shared scene revision; deterministic ordering; partial-failure cleanup; no false physical/render certification.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0329_CODEX_PROMPT_V01.md
