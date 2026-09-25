# PL-0135 — Codex Work Order V01

Task: **PL-0135 — PySide6 application shell**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0135_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. M03–M05 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M07.

M06 hosts existing M05 Windows services; do not duplicate ingest, validation, quarantine, raw-store, receiver or transfer logic.

## Mandatory implementation

1. Add PySide6 as a declared/locked runtime dependency compatible with Python 3.12 and record any required license/dependency metadata.
2. Create one production PackLab Studio application entry point with QApplication ownership, organization/app identifiers, icon/resource hooks, exception boundary and deterministic exit code.
3. Keep domain/services in packlab_core or existing packlab_studio services; do not move business logic into widgets.
4. Support headless/offscreen test execution without requiring a physical display.
5. Add shell smoke tests proving app construction, one main window, clean close and no import-time QApplication side effects.

## Validation

Use PySide6 offscreen/headless tests where practical. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Any dependency change must update pyproject.toml and uv.lock reproducibly. Create one implementation/evidence commit and a separate log-only commit. User-facing repository links must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
