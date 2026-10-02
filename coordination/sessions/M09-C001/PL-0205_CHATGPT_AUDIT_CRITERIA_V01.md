# PL-0205 - ChatGPT Audit Criteria V01

Task: **Detect object ground/base plane with user override**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0205_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Implement deterministic base/ground-plane candidate detection from captured object geometry using a bounded robust policy, with evidence/confidence and an explicit manual override contract. Automatic results are candidates, not hidden truth. Overrides must be versioned/provenance-bound and never mutate source geometry. Do not perform upright/front selection beyond the plane normal needed by this child.
3. Public-boundary tests cover at minimum: flat synthetic base, noisy/outlier cloud, ambiguous/no-plane, threshold boundaries, override acceptance/rejection, parent revision invalidation, source immutability.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no unsupported physical/metric claim is made.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M10+ implementation is introduced. Owner-controlled physical evidence is never fabricated.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and the child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Audit must independently inspect the actual GitHub diff/source/evidence. Builder validation is not acceptance. A real failed/blocked/owner-required child stops the M09 batch.
