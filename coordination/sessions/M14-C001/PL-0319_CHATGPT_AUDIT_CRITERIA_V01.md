# PL-0319 - ChatGPT Audit Criteria V01

Task: **Separate geometry material from product liquid/content appearance**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 material-authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement separate immutable assignment contracts for package/component geometry material versus product liquid/content appearance. These channels must not overwrite each other and must bind to stable component IDs/source revisions.
3. Tests/evidence cover at minimum: geometry-only assignment; content-only appearance; combined state; replacement/removal; component binding; deterministic revisioning; no cross-channel overwrite; no geometry mutation; no inferred fill volume or formulation property.
4. Exact Design Model/component provenance is preserved and all material/PBR/PCR values remain visual/design metadata unless explicit external certification authority is separately supplied.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0319_CODEX_PROMPT_V01.md
