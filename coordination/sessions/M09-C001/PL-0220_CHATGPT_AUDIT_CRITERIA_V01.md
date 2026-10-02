# PL-0220 - ChatGPT Audit Criteria V01

Task: **Measure dimension error on matte bottle, glossy bottle and jerrycan**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0220_CODEX_PROMPT_V01.md

All criteria are mandatory for a completed child.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation/evidence is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Execute the M09 physical accuracy benchmark using owner-controlled caliper ground truth and corresponding authorized PackLab scan/measurement evidence for at least matte bottle, glossy bottle and jerrycan. Compute per-dimension signed/absolute/relative errors and aggregate statistics with complete provenance. Synthetic or nominal dimensions are not substitutes for physical ground truth.
3. Public-boundary tests/evidence cover at minimum: all three required object classes, ground-truth binding, per-dimension error math, missing/rejected sample accounting, deterministic aggregates, no nominal/synthetic substitution.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no scale/physical claim exceeds PL-0209 provenance.
5. Physical completion requires authorized owner-controlled measurements/scans/records. Synthetic, nominal or generated substitutes are an automatic FAIL for a claimed completed child. No unreviewed dependency/model/hosted service/private publication/later-child or M10+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and a completed child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

A real physical-evidence absence is not an audit failure when the builder truthfully stops the master batch as OWNER_REQUIRED before claiming child completion. Audit must independently inspect actual GitHub diff/source/evidence.
