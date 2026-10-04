# PL-0320 - ChatGPT Audit Criteria V01

Task: **Implement PBR parameters: base color, roughness, transmission/opacity, IOR and normal detail where supported**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 material-authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement bounded deterministic PBR visual parameter contracts for base color, roughness, transmission/opacity, IOR and optional normal-detail metadata. Validate numeric domains and explicitly mark all values as render appearance parameters rather than measured material properties.
3. Tests/evidence cover at minimum: valid parameter ranges; finite-number rejection; mutually coherent opacity/transmission policy; IOR bounds; normal-detail reference metadata; deterministic serialization; visual-only disclaimer; no certified optical/material property claim.
4. Exact Design Model/component provenance is preserved and all material/PBR/PCR values remain visual/design metadata unless explicit external certification authority is separately supplied.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0320_CODEX_PROMPT_V01.md
