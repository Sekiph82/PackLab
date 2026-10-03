# PL-0284 - ChatGPT Audit Criteria V01

Task: **Implement tube fitting from scan/reference dimensions**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Fit the M12 tube parametric family from an exact Scan Master when available and/or explicitly supplied reference dimensions with source authority labels. Keep captured measurements, user/reference dimensions and modeled parameters distinct. Missing flexible-wall regions remain uncertain; no hidden wall-thickness or material deformation inference.
3. Tests/evidence cover at minimum: scan-bound fit, explicit reference-dimension fit, mixed source provenance, missing/contradictory evidence, mm_unverified semantics, no wall-thickness/material inference.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0284_CODEX_PROMPT_V01.md
