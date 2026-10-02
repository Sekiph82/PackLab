# PL-0206 - ChatGPT Audit Criteria V01

Task: **Implement upright alignment with manual correction**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0206_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Using the accepted base-plane evidence, compute a deterministic non-destructive rotation that aligns the accepted object-up direction to canonical +Z. Provide a manual correction/override seam with explicit actor/evidence. Reject degenerate/ambiguous inputs. Do not bake geometry and do not choose front direction in this child.
3. Public-boundary tests cover at minimum: already-upright, tilted object, antiparallel/degenerate normals, deterministic quaternion/matrix, manual correction, parent invalidation, non-destructive behavior.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no unsupported physical/metric claim is made.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M10+ implementation is introduced. Owner-controlled physical evidence is never fabricated.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and the child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Audit must independently inspect the actual GitHub diff/source/evidence. Builder validation is not acceptance. A real failed/blocked/owner-required child stops the M09 batch.
