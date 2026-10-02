# PL-0202 - ChatGPT Audit Criteria V01

Task: **Detect calibration markers and bind them to reconstructed cameras**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0202_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Reuse the accepted PackLab marker detector and marker policy. Create a deterministic observation-to-camera association contract keyed by source image asset ID/digest and camera solution revision. Preserve ordered image-pixel corners and detector provenance. Reject missing, duplicate, stale, dimension-mismatched or ambiguous image/camera bindings. This child detects/associates only: it does not infer physical scale or promote metric authority.
3. Public-boundary tests cover at minimum: synthetic marker association, duplicate/missing camera identity, source digest mismatch, corner/coordinate preservation, deterministic serialization, unavailable OpenCV, source immutability.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no unsupported physical/metric claim is made.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M10+ implementation is introduced. Owner-controlled physical evidence is never fabricated.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and the child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Audit must independently inspect the actual GitHub diff/source/evidence. Builder validation is not acceptance. A real failed/blocked/owner-required child stops the M09 batch.
