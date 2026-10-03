# PL-0273 - ChatGPT Audit Criteria V01

Task: **Constrain cage edits to preserve key dimensions and symmetry**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Add constraints for cage/freeform edits so selected key dimensions, mating references and enabled symmetry relationships remain preserved within exact numerical rules. Reject edits that violate protected dimensions or impossible constraints; never silently relax them. Record constrained/unconstrained degrees of freedom and residual diagnostics.
3. Tests/evidence cover at minimum: protected height/width/depth, symmetry on/off, valid local deformation, violating deformation rejection, mating-reference preservation, deterministic residuals, undo/redo compatibility.
4. Scan Master remains immutable; Design Model/freeform/preview layers preserve exact parent/unit/deferred authority and never become captured or physical manufacturing truth.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final child log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0273_CODEX_PROMPT_V01.md
