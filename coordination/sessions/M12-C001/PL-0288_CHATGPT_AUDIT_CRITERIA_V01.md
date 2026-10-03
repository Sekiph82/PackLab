# PL-0288 - ChatGPT Audit Criteria V01

Task: **Add package-family selection and conversion safeguards**

All criteria are mandatory.

1. M12 tracker/master authorization, safe synchronization, M11 AUDITED_PASS and M09 physical deferral were read.
2. Deterministic PackLab-owned implementation is limited to: Implement explicit package-family selection/conversion rules across supported M11/M12 families (bottle/jar, jerrycan, tube, flexible pack). Conversion must be intentional, versioned and only allowed when semantic features/parameters have an explicit mapping; unsupported features are reported, never silently discarded. Preserve original revisions and Scan Master parent binding where applicable.
3. Tests/evidence cover at minimum: same-family no-op, supported bottle-to-jerrycan-style conversion where mapping explicit, unsupported handle/closure/flexible feature reporting, original revision preservation, exact parent binding, deterministic conversion revision.
4. Scan Master/Design Model/assembly/library/flexible-pack authority boundaries and inherited scale/deferred-validation state remain explicit; no hidden physical/manufacturing truth is invented.
5. No unreviewed CAD/backend/dependency/private/unlicensed asset/later-child or M13+ implementation is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation/log publication is separate; final log ends `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0288_CODEX_PROMPT_V01.md
