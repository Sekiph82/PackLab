# PL-0155 — Codex Work Order V01

Task: **PL-0155 — Wireframe, normals and point-cloud debug modes**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0155_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

Use the single viewport backend/adapter selected by PL-0151. Display/debug/LOD/export representations must never overwrite authoritative source geometry.

## Mandatory implementation

1. Implement viewport debug/render modes for solid/surface baseline, wireframe, normals visualization and point-cloud rendering using the selected PL-0151 backend.
2. Modes must be scene/view state only and never mutate source mesh/point-cloud data.
3. Normals display must handle missing normals truthfully and either compute a temporary derived view representation or report unavailable without persisting fake authority.
4. Expose mode toggles through a backend-independent viewport state interface.
5. Add tests for mode transitions, persistence/state serialization, missing-normal behavior, source non-mutation and one real backend/offscreen smoke path.

## Validation

Use offscreen/headless tests where supported and truthfully record unavailable native/GPU capabilities. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
