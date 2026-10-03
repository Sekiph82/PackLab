# PL-0260 - ChatGPT Audit Criteria V01

Task: **Save fitting preset and parameters independently of raw scan**

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0260_CODEX_PROMPT_V01.md

All criteria are mandatory.

1. M11 tracker/master authorization, accepted M10 predecessor and M09 deferral were read and synchronization was safe.
2. Deterministic PackLab-owned implementation is limited to: Define deterministic versioned fitting presets containing strategy, fitting algorithm parameters, constraints and reusable package-family defaults without embedding raw scan bytes or project-private geometry. Applying a preset to a different Scan Master creates new project-specific fitting evidence and does not copy parent IDs or claim identical fit quality.
3. Tests cover at minimum: preset round-trip, canonical serialization, apply to new parent, no raw scan/geometry bytes, parameter/version validation, stale/unsupported preset rejection, no copied fit-quality claim.
4. Exact Scan Master parent remains immutable; Design Model is separate parametric authority; derived preview/deviation evidence does not become Scan Master or manufacturing truth; scale/deferred status is preserved.
5. No unreviewed CAD/backend/dependency/private evidence/later-child or M12+ work is introduced.
6. Focused/full/static/scope/security/remote evidence is truthful; implementation and log publication are separate; log ends `READY_FOR_INDEPENDENT_AUDIT`.

Independent audit inspects actual source/diff/evidence; builder validation is not acceptance.
