# PL-0137 — Codex Work Order V01

Task: **PL-0137 — Dockable logical workspace layout**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0137_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. M03–M05 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M07.

M06 hosts existing M05 Windows services; do not duplicate ingest, validation, quarantine, raw-store, receiver or transfer logic.

## Mandatory implementation

1. Build a QMainWindow-based workspace with central content plus logical dock areas suitable for viewport, properties/inspector, scene/object tree, job/activity and logs.
2. Define stable dock/object names so Qt saveState/restoreState can work across sessions.
3. Provide default layouts per major workspace without coupling dock logic to future reconstruction/editor implementations.
4. Prevent duplicate dock instances and invalid docking relationships.
5. Add tests for default dock inventory, stable object names, show/hide/move state and deterministic reset-to-default.

## Validation

Use PySide6 offscreen/headless tests where practical. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Any dependency change must update pyproject.toml and uv.lock reproducibly. Create one implementation/evidence commit and a separate log-only commit. User-facing repository links must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
