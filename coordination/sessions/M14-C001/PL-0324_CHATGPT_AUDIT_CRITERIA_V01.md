# PL-0324 - ChatGPT Audit Criteria V01

Task: **Integrate Blender headless executable discovery and version probe**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 Blender/render authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement deterministic Blender executable discovery/probe for an explicit configured path plus safe platform discovery where appropriate. Probe via offline headless/version command with timeout, capture exact version/build facts, and expose READY/UNAVAILABLE/INCOMPATIBLE diagnostics. Do not download Blender. If no real usable Blender executable is available at execution time, publish truthful blocker evidence and stop the M14 master before Blender-dependent children.
3. Tests/evidence cover at minimum: configured executable; missing path; non-executable/wrong binary; timeout; version parse; supported-version policy; no network/download; privacy-safe diagnostics; subprocess argument safety; real capability smoke when executable is available.
4. Any mandatory Blender-dependent smoke uses the real approved executable; fake/unit fixtures cannot substitute for required real render/export evidence. Derived renders/GLB never replace Design Model/CAD authority.
5. No auto-download, unreviewed dependency, private evidence, ambient path leakage, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0324_CODEX_PROMPT_V01.md
