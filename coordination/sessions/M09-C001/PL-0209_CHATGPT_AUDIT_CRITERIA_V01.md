# PL-0209 - ChatGPT Audit Criteria V01

Task: **Persist scale provenance, uncertainty and scale-state promotion rules**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0209_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Implement the mandatory ScaleProvenance contract and explicit RELATIVE / METRIC_UNVERIFIED / METRIC_VERIFIED state machine. Promotion to METRIC_VERIFIED requires accepted owner-controlled physical scale evidence; nominal SVG values, synthetic fixtures, neural metric depth and unverified printer output cannot promote. Persist calibration observation IDs, physical reference and units, scale factor, residuals, rejected observations, algorithm version, parent reconstruction, uncertainty, timestamp and actor/process provenance. Parent changes invalidate derived scale.
3. Public-boundary tests cover at minimum: relative cannot claim mm, verified/unverified promotion rules, rejected evidence exclusion, parent invalidation, persistence/reopen, AI_VISUAL_REFERENCE isolation, deterministic factor application.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no unsupported physical/metric claim is made.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M10+ implementation is introduced. Owner-controlled physical evidence is never fabricated.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and the child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Audit must independently inspect the actual GitHub diff/source/evidence. Builder validation is not acceptance. A real failed/blocked/owner-required child stops the M09 batch.
