# PL-0309 - ChatGPT Audit Criteria V01

Task: **Validate drawing dimensions against Design Model numerical values**

All criteria are mandatory.

1. M13 authorization, safe synchronization, M12 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic implementation is limited to: Implement independent numerical consistency validation between technical drawing dimension entities/section annotations and the exact source Design Model/CAD representation values. Recompute expected overall/neck/selected-feature dimensions from source numerical geometry and compare to drawing entities with an explicit software/numerical tolerance. Validate unit labels, parent revisions and title-block revision references. This is software consistency checking, not physical metrology. Reject stale drawing/source pairs, unit mismatch and dimensions derived from pixel/render measurements.
3. Tests/evidence cover at minimum: matching known dimensions; tampered dimension value; stale model/CAD revision; unit-label mismatch; relative/mm_unverified handling; selected feature dimension; deterministic validation report; software tolerance != physical tolerance.
4. Exact Design Model/CAD parent revisions and units remain explicit; no pixel-derived dimensions, RELATIVE->mm promotion or physical/mold/manufacturing claim occurs.
5. No unreviewed dependency/private evidence/later-child or M14+ implementation is introduced; PL-0308 must block rather than silently add a PDF dependency.
6. Focused/full/static/security/scope/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0309_CODEX_PROMPT_V01.md
