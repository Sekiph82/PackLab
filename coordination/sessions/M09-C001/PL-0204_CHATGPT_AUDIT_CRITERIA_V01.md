# PL-0204 - ChatGPT Audit Criteria V01

Task: **Define canonical PackLab metric coordinate-frame contract**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0204_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, repository synchronization, accepted M08 predecessor and mandatory pre-reads were present before implementation.
2. The implementation is deterministic, PackLab-owned, provenance-bound and limited to this frozen scope: Define the canonical normalized frame contract without yet selecting an object's actual front/upright transform: right-handed PackLab axes, Z-up, explicit front-axis convention, millimetre unit semantics only when scale state permits, transform composition/order and provenance. RELATIVE geometry must never be mislabeled mm. Keep this a contract/normalization foundation for PL-0205 through PL-0209.
3. Public-boundary tests cover at minimum: right-handed axes, transform round-trip/composition, relative-vs-mm rejection, invalid/non-finite transforms, deterministic serialization.
4. RAW_CAPTURE, accepted M08 authority/revisions and source bytes remain immutable; no AI/generated geometry gains measurement authority and no unsupported physical/metric claim is made.
5. No unreviewed dependency/model/hosted service/private evidence/later-child or M10+ implementation is introduced. Owner-controlled physical evidence is never fabricated.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation and log commits are separate, and the child log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Audit must independently inspect the actual GitHub diff/source/evidence. Builder validation is not acceptance. A real failed/blocked/owner-required child stops the M09 batch.
