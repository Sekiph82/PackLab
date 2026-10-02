# PL-0213 - ChatGPT Audit Criteria V01

Task: **Extract horizontal cross-sections at arbitrary Z**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0213_CODEX_PROMPT_V01.md

All criteria are mandatory for a completed child.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation/evidence is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Implement deterministic horizontal cross-section extraction from normalized captured geometry at an explicit canonical Z with a bounded slab/intersection policy. Preserve parent geometry/scale identity, return ordered section evidence and reject stale, empty, non-finite or out-of-range requests. Do not invent surface closure where the captured evidence is incomplete.
3. Public-boundary tests/evidence cover at minimum: synthetic box/cylinder sections, exact boundary Z, empty/no-hit section, bounded slab policy, ordering determinism, relative/metric unit labeling, stale provenance.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no scale/physical claim exceeds PL-0209 provenance.
5. No owner-controlled physical evidence may be fabricated or inferred. No unreviewed dependency/model/hosted service/private publication/later-child or M10+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and a completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

A real physical-evidence absence is not an audit failure when the builder truthfully stops the master batch as OWNER_REQUIRED before claiming child completion. Audit must independently inspect actual GitHub diff/source/evidence.
