# PL-0279 - ChatGPT Audit Criteria V01

Task: **Model dip tube as parameterized length/diameter path**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement a backend-neutral parametric dip-tube component with path, length, diameter and attachment references. Support straight and bounded piecewise-smooth path representation, explicit unit state and collision-independent editing. Validate positive diameter/length, path continuity and attachment compatibility. Do not infer unseen dip-tube dimensions from scan evidence.
3. Tests/evidence cover at minimum: straight/curved path, positive length/diameter, discontinuous/degenerate path rejection, attachment reference, unit/deferred status, deterministic component revision, no hidden scan inference.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0279_CODEX_PROMPT_V01.md
