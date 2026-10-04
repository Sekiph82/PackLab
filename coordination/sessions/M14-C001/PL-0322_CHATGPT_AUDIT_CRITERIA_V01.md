# PL-0322 - ChatGPT Audit Criteria V01

Task: **Add PCR metadata and visual variants without implying certified material properties**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 material-authority rules are evidenced truthfully.
2. Implementation scope is limited to: Add bounded PCR declaration/visual-variant metadata that can record user-supplied or design-intent recycled-content percentages and appearance variants while explicitly separating declared/design metadata from verified certification.
3. Tests/evidence cover at minimum: 0/100 boundaries; invalid percentages; source/status enum such as DESIGN_INTENT/DECLARED/VERIFIED_EXTERNAL_REFERENCE only when explicit external authority is supplied; visual variants; deterministic identity; no automatic certification; no regulatory/environmental-performance claim.
4. Exact Design Model/component provenance is preserved and all material/PBR/PCR values remain visual/design metadata unless explicit external certification authority is separately supplied.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0322_CODEX_PROMPT_V01.md
