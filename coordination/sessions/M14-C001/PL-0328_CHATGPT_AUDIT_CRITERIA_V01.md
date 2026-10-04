# PL-0328 - ChatGPT Audit Criteria V01

Task: **Render transparent-background product image**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement real Blender headless transparent-background still rendering from the accepted scene/preset contract. Record render engine/version/settings, input digests, output digest and semantic validation. Determinism means reproducible settings/provenance, not guaranteed byte-identical pixels across hardware.
3. Tests/evidence cover at minimum: real render produces non-empty image with alpha; expected dimensions; object visible/not clipped; transparent background; source/settings manifest; failure/timeout handling; no temp-path leakage; no physical/material authority escalation.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0328_CODEX_PROMPT_V01.md
