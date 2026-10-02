# PL-0217 - ChatGPT Audit Criteria V01

Task: **Propagate and display measurement uncertainty/confidence**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0217_CODEX_PROMPT_V01.md

All criteria are mandatory for a completed child.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation/evidence is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Define PackLab-owned uncertainty propagation/reporting across scale, normalization and measurement outputs. Keep uncertainty numeric/evidence-based where known and explicitly unknown otherwise. Combine only compatible uncertainty sources under a documented method; never convert heuristic confidence into physical tolerance. Provide a presentation-ready contract without making UI own truth.
3. Public-boundary tests/evidence cover at minimum: known propagated uncertainty, missing uncertainty, relative geometry, incompatible units, deterministic serialization, no false precision, measurement linkage.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no scale/physical claim exceeds PL-0209 provenance.
5. No owner-controlled physical evidence may be fabricated or inferred. No unreviewed dependency/model/hosted service/private publication/later-child or M10+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and a completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

A real physical-evidence absence is not an audit failure when the builder truthfully stops the master batch as OWNER_REQUIRED before claiming child completion. Audit must independently inspect actual GitHub diff/source/evidence.
