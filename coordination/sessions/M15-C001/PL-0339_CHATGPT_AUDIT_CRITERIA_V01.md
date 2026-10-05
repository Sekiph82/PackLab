# PL-0339 - ChatGPT Audit Criteria V01

Task: **Grid/list Packaging Library browser**

All criteria are mandatory.

1. Route.LIBRARY is a real view, not placeholder, and works without an open project.
2. Grid/list modes show stable asset ID/name/core metadata and thumbnail/placeholder.
3. UI consumes accepted library service/domain APIs rather than mutating canonical JSON directly.
4. No remote image fetch; thumbnail paths are safely resolved through injected local authority.
5. Selection/refresh/mode changes are deterministic and do not mutate source metadata.
6. Headless PySide tests cover route integration, empty/error states, thumbnail fallback and selection.

7. Scope remains inside PL-0339 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0339_CODEX_PROMPT_V01.md
