# PL-0331 - ChatGPT Audit Criteria V01

Task: **Record render settings and Blender version for reproducibility**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement the final canonical M14 render provenance record shared by stills and GLB: exact Blender executable/version/build, PackLab commit/version, scene-package revision, source model/CAD/label/artwork/material revisions and digests, render engine/device/settings, camera/light preset IDs, output digests and explicit limitations. Canonical identity must exclude ambient paths/timestamps where inappropriate.
3. Tests/evidence cover at minimum: stills+GLB provenance; exact Blender/PackLab versions; source revision/digest binding; render engine/device/settings; camera/light IDs; output digests; deterministic identity; privacy-safe path handling; explicit cross-hardware pixel-identity limitation; no physical/material/production authority escalation.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0331_CODEX_PROMPT_V01.md
