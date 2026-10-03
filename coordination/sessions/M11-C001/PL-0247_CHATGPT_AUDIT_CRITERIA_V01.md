# PL-0247 - ChatGPT Audit Criteria V01

Task: **Implement undo/redo command model for parametric edits**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0247_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. Live tracker/master authorization, safe synchronization, accepted M10 predecessor and M09 owner physical-validation deferral were read before implementation.
2. Implementation is deterministic, PackLab-owned/provenance-bound and limited to: Implement immutable command-based undo/redo for Design Model edits. Each command must declare expected model revision, targeted parameter/feature and before/after values; application creates a new revision. Undo/redo must be deterministic, bounded and never mutate history or Scan Master parents. Concurrent/stale commands fail closed.
3. Tests/evidence cover at minimum: edit/undo/redo round-trip, multi-command history, redo invalidation after branch edit, stale expected revision, deleted feature target, deterministic command IDs, parent binding preserved.
4. Scan Master remains immutable parent authority; Design Model is separate parametric truth; preview meshes remain derived proxies; inherited scale/deferred-validation state cannot become physical/mold authority.
5. No unreviewed dependency/CAD backend/model/hosted/private evidence/later-child or M12+ implementation is introduced.
6. Focused/full/static/security/scope/remote evidence is truthful, implementation/log commits are separate and child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Audit must inspect actual GitHub source/diff/evidence. Builder validation is not audit acceptance.
