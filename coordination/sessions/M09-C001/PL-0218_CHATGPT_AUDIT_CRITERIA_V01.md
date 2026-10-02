# PL-0218 - ChatGPT Audit Criteria V01

Task: **Export measurement report with units and provenance**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0218_CODEX_PROMPT_V01.md

All criteria are mandatory for a completed child.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation/evidence is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Implement deterministic human/machine-readable measurement report export over accepted M09 measurement artifacts. Include project/source/geometry/scale revisions, units, uncertainty, method/version and explicit authority/limitation statements. Exclude private raw bytes and ambient identity. Reject stale/mixed-parent measurements and never claim certified or mold-ready output.
3. Public-boundary tests/evidence cover at minimum: mixed measurement types, deterministic ordering/serialization, stale parent rejection, relative-vs-metric labeling, uncertainty fields, privacy/redaction, no certified claim.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no scale/physical claim exceeds PL-0209 provenance.
5. No owner-controlled physical evidence may be fabricated or inferred. No unreviewed dependency/model/hosted service/private publication/later-child or M10+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and a completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

A real physical-evidence absence is not an audit failure when the builder truthfully stops the master batch as OWNER_REQUIRED before claiming child completion. Audit must independently inspect actual GitHub diff/source/evidence.
