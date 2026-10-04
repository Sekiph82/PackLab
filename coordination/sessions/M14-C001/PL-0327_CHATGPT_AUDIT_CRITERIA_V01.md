# PL-0327 - ChatGPT Audit Criteria V01

Task: **Create standard studio-lighting/camera presets for packaging mockups**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement deterministic named studio-lighting and camera presets for packaging mockups, including front/three-quarter/back framing rules derived from scene bounds. Presets are presentation metadata only and must be reproducible from a versioned contract.
3. Tests/evidence cover at minimum: preset IDs/version; front/three-quarter/back camera transforms; deterministic bounds-based framing; lighting parameters; transparent/background compatibility; finite/bounded values; real Blender scene smoke; source revisions retained; no physical measurement inference.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0327_CODEX_PROMPT_V01.md
