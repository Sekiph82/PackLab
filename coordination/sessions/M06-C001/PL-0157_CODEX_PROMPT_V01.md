# PL-0157 — Codex Work Order V01

Task: **PL-0157 — Large-mesh benchmark and viewport LOD strategy**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0157_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

Use the single viewport backend/adapter selected by PL-0151. Display/debug/LOD/export representations must never overwrite authoritative source geometry.

## Mandatory implementation

1. Create a reproducible M06 large-mesh/point-cloud benchmark using synthetic or repository-safe generated fixtures at multiple sizes representative of packaging scans.
2. Measure load time, scene initialization, memory proxy/observation and interaction/render proxy where the environment permits; record hardware/backend/runtime metadata.
3. Define and implement an initial viewport LOD/decimation/display-budget strategy that affects only interactive display representations and never overwrites authoritative source geometry.
4. LOD selection must be deterministic from scene size/performance policy and expose current display-vs-source counts for diagnostics.
5. Add tests for LOD threshold selection, source non-mutation, stable display counts, fallback when decimation unavailable and benchmark result schema.
6. Publish an M06 performance evidence artifact with truthful limitations; do not claim physical GPU performance if only software/offscreen rendering was available.

## Validation

Use offscreen/headless tests where supported and truthfully record unavailable native/GPU capabilities. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
