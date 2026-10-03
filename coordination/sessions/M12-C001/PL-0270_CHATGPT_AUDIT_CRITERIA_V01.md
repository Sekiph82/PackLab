# PL-0270 - ChatGPT Audit Criteria V01

Task: **Model handle opening as editable constrained feature**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Create an editable parametric handle-opening feature from an accepted PL-0269 candidate. Represent opening profile/path/clearance envelope and relationship to jerrycan body as versioned Design Model parameters/features. The opening is modeling geometry, not copied scan triangles. Apply explicit constraints to keep it inside supported body regions and reject impossible/self-intersecting states.
3. Tests/evidence cover at minimum: valid opening feature, move/resize edit, body-bound constraints, self-intersection/out-of-body rejection, stable feature identity, undo/redo compatibility, no Scan Master mutation.
4. Scan Master remains immutable; Design Model/freeform/preview layers preserve exact parent/unit/deferred authority and never become captured or physical manufacturing truth.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0270_CODEX_PROMPT_V01.md
