# PL-0152 — Codex Work Order V01

Task: **PL-0152 — Mesh/point-cloud loading and orbit/pan/zoom**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0152_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

For PL-0151/0152, use measured local evidence and a single viewport adapter boundary. Do not hard-code the rest of Studio to an experimental backend before the spike decision is frozen.

## Mandatory implementation

1. Implement the selected PL-0151 viewport adapter behind a PackLab viewport interface owned by Studio, not directly coupled throughout widgets.
2. Load supported local mesh/point-cloud fixture formats sufficient for M06 foundation; preserve units/coordinates without modifying source files.
3. Implement camera orbit, pan, zoom, fit-to-view and reset with deterministic state serialization where practical.
4. Handle empty/corrupt/unsupported files with structured errors and keep UI responsive for bounded fixture sizes.
5. Add offscreen/headless-capable tests for load metadata, scene bounds, camera transforms, fit/reset and failure handling plus one real adapter smoke test.

## Validation

Use deterministic filesystem/offscreen tests and reproducible benchmark commands. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Declare/lock any viewport dependency and record license impact. Create one implementation/evidence commit and separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
