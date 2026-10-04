# PL-0305 - ChatGPT Audit Criteria V01

Task: **Add dimension annotations for overall H/W/D, neck and selected features**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement deterministic drawing-dimension entities for overall H/W/D, neck/finish dimensions and user-selected stable Design Model/CAD features. Dimension values must come from exact Design Model/CAD numerical geometry, not screen pixels. Preserve source unit state: RELATIVE uses reconstruction_units and must not display 'mm'; METRIC_UNVERIFIED may display numerical mm with an explicit unverified marker/disclaimer. Define extension lines, arrows/text anchors and collision-safe placement metadata without baking typography into domain truth. Reject stale/missing feature references.
3. Tests/evidence cover at minimum: overall H/W/D; neck/feature dimension; RELATIVE unit label; mm_unverified label; stale feature rejection; deterministic anchors; negative/zero impossible dimension rejection; assembly component dimension.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0305_CODEX_PROMPT_V01.md
