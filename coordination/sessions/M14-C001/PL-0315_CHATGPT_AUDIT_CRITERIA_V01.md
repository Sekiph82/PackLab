# PL-0315 - ChatGPT Audit Criteria V01

Task: **Import SVG/PNG artwork and map it non-destructively to a Label Zone**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement bounded offline SVG/PNG artwork ingest as a separate artwork asset contract with digest/media metadata, then map it non-destructively to an existing Label Zone. Artwork must never become Design Model/CAD authority.
3. Tests/evidence cover at minimum: SVG and PNG validation; malformed/oversized input rejection; digest identity; no embedded remote fetch; mapping transform/crop/fit metadata; zone independence; artwork replacement without zone revision mutation; privacy-safe path handling.
4. Exact Design Model/CAD/Label Zone/artwork provenance as applicable is preserved; RELATIVE is never promoted to mm and mm_unverified never becomes physical/production authority.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0315_CODEX_PROMPT_V01.md
