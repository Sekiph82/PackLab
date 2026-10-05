# PL-0335 - ChatGPT Audit Criteria V01

Task: **Reusable caps, triggers and pumps**

All criteria are mandatory.

1. Stable reusable component records exist for CAP/TRIGGER/PUMP.
2. Many-to-many compatibility links are deterministic and reference exact body/component IDs.
3. Compatibility provenance is explicit; visual/estimated compatibility is never supplier-certified fit.
4. Stale/deleted body/component references and duplicate links reject.
5. Revisions are immutable and bounded.
6. Tests cover shared components, incompatible provenance combinations and no-fit-certification claims.

7. Scope remains inside PL-0335 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0335_CODEX_PROMPT_V01.md
