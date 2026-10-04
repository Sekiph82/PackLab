# PL-0306 - ChatGPT Audit Criteria V01

Task: **Add technical drawing title block with package ID, revision, units and disclaimer**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement a deterministic title-block data contract for technical drawings containing package/project ID, Design Model revision, CAD representation revision, parent-authority kind, drawing revision, units/scale state, selected binding/kernel/PackLab versions, generated-view list, timestamp only as presentation metadata, and mandatory authority disclaimer. For mm_unverified, disclaimer must say numerical dimensions are unverified against physical benchmark and not mold/manufacturing approval. For RELATIVE, disclaimer must say dimensions are reconstruction-relative. Do not include private ambient paths or user machine identity.
3. Tests/evidence cover at minimum: scan-bound and standalone title blocks; relative/mm_unverified disclaimers; deterministic core metadata; revision/version fields; privacy-safe output; no machine/user path; no certification claim.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0306_CODEX_PROMPT_V01.md
