# PL-0256 - ChatGPT Audit Criteria V01

Task: **Add front/back and left/right symmetry constraints with user toggle**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0256_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Implement explicit editable symmetry constraints on Design Model features/sections for front-back and left-right axes. Toggling constraints creates new model revisions, never rewrites history. Constraint application must preserve canonical axes, reject conflicting/impossible edits and expose when scan evidence disagrees with the chosen modeling constraint.
3. Tests cover at minimum: LR/FB/both/none toggles, mirrored parameter propagation, conflicting constraints, evidence disagreement flag, undo/redo compatibility, deterministic revision.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
