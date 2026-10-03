# PL-0258 - ChatGPT Audit Criteria V01

Task: **Allow user edits to height/width/depth while maintaining parameter relationships**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0258_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Implement domain edit commands for overall height/width/depth that update the parametric model while preserving defined feature relationships, symmetry and explicit constraints. Edits create new revisions and must reject impossible or underdetermined parameter states rather than silently distort unrelated features. UI may call the service but must not own geometry truth.
3. Tests cover at minimum: height/width/depth edit, proportional/constraint propagation, symmetry preservation, impossible edit rejection, undo/redo, stable feature IDs, parent Scan Master unchanged.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
