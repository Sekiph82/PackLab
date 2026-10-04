# PL-0318 - ChatGPT Audit Criteria V01

Task: **Define material-library schema for HDPE, PET, PP and other packaging materials**

All criteria are mandatory.

1. Authorization/predecessor reads and M14 material-authority rules are evidenced truthfully.
2. Implementation scope is limited to: Implement an immutable deterministic visual material-library schema with stable IDs, material family, display metadata, PBR-ready fields, provenance/source classification, and explicit NON_CERTIFIED_VISUAL_REFERENCE semantics. Include starter schema support for HDPE, PET, PP and extensible other packaging materials without embedding regulatory claims.
3. Tests/evidence cover at minimum: schema validation; stable IDs; duplicate rejection; deterministic serialization; HDPE/PET/PP/OTHER families; bounded strings/numbers; explicit visual-only authority flags; no certified physical/regulatory property inference.
4. Exact Design Model/component provenance is preserved and all material/PBR/PCR values remain visual/design metadata unless explicit external certification authority is separately supplied.
5. No unreviewed dependency, network/runtime download, private evidence, tracker edit, later-child implementation, or M15+ work is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/evidence and child-log commits are distinct; child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M14-C001/PL-0318_CODEX_PROMPT_V01.md
