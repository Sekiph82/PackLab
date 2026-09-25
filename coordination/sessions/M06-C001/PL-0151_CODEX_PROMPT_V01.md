# PL-0151 — Codex Work Order V01

Task: **PL-0151 — 3D viewport technology performance spike**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0151_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

For PL-0151/0152, use measured local evidence and a single viewport adapter boundary. Do not hard-code the rest of Studio to an experimental backend before the spike decision is frozen.

## Mandatory implementation

1. Perform and document a focused comparison of PySide6-compatible 3D viewport approaches appropriate for point clouds/meshes on Windows, considering Qt integration, Python 3.12 support, licensing, headless/offscreen testing, large-mesh performance, picking, wireframe/normals and future CAD coexistence.
2. At minimum compare two viable approaches; one may be VTK/PyVista-family and another Qt/OpenGL/other supported stack if available.
3. Build minimal executable spikes using representative synthetic point/triangle counts, not marketing claims.
4. Record measured startup/load/render or interaction proxy metrics, memory observations, dependency weight and limitations on the available Windows host.
5. Select one M06 viewport approach with a written ADR/decision artifact; do not implement M07 reconstruction here.
6. Add a reproducible benchmark/spike command that can run headless where supported and truthfully records unavailable GPU/native capabilities.

## Validation

Use deterministic filesystem/offscreen tests and reproducible benchmark commands. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Declare/lock any viewport dependency and record license impact. Create one implementation/evidence commit and separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
