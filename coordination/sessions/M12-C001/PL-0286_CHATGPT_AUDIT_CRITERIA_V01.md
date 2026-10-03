# PL-0286 - ChatGPT Audit Criteria V01

Task: **Implement front/back flexible-pack surfaces and seal-zone representation**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement deterministic editable front/back surface and perimeter/seal-zone representation for flexible packs, with stable feature IDs, artwork coordinate frame and explicit simplified geometry assumptions. Surfaces may be planar or bounded simplified bulge representations but must not imply measured film deformation. Preserve design-only authority.
3. Tests/evidence cover at minimum: front/back surfaces, top/bottom/side seals, artwork coordinates, simple bulge optional path, invalid crossing/negative seal widths, deterministic preview, design-only limitation.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0286_CODEX_PROMPT_V01.md
