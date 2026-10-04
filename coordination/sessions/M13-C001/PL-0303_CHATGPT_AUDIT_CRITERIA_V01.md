# PL-0303 - ChatGPT Audit Criteria V01

Task: **Generate front/side/top orthographic views from Design Model**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement a backend-neutral technical-drawing view model that derives front, side and top orthographic projections from the exact Design Model/CAD representation. Projection axes must be tied to PackLab canonical +X/+Y/+Z semantics and explicit front direction where applicable. Produce vector-ready geometry primitives/curves/edges with deterministic view bounds and scale metadata. Hidden-line handling may be supported only if deterministic through the CAD adapter; otherwise expose explicit visible-edge-only limitations. Do not rasterize as the source of truth.
3. Tests/evidence cover at minimum: front/side/top known box/cylinder/bottle; canonical orientation; deterministic view extents; visible-edge/hidden-line policy; stable feature references; scan-bound/standalone parent propagation; vector-source authority.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0303_CODEX_PROMPT_V01.md
