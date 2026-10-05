# PL-0342 - ChatGPT Audit Criteria V01

Task: **Asset detail page with 3D preview and revisions**

All criteria are mandatory.

1. Detail page shows requested metadata, dimensions, revisions and linked artwork/SKU/component relationships.
2. 3D preview reuses existing PackLab viewport adapter and exact runtime-resolved/digest-checked artifact.
3. Missing/stale/unavailable linked project data is visible and fail-safe, not silently replaced.
4. No absolute project root enters canonical library identity/state.
5. Preview is read-only and does not mutate project/geometry authority.
6. Headless UI tests cover available preview, missing preview, revision list, artwork links and provenance labels.

7. Scope remains inside PL-0342 and accepted predecessor seams; no later-child/M16+ implementation.
8. Focused/full/static/security/dependency/remote evidence is truthful; implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0342_CODEX_PROMPT_V01.md
