# PL-0139 — Codex Work Order V01

Task: **PL-0139 — Global job/activity panel**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0139_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0139_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0139_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. M03–M05 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M07.

M06 hosts existing M05 Windows services; do not duplicate ingest, validation, quarantine, raw-store, receiver or transfer logic.

## Mandatory implementation

1. Create a central JobManager/domain model and UI panel for long-running work with stable job IDs, title/type, queued/running/succeeded/failed/cancelling/cancelled states, progress, timestamps and bounded log/status messages.
2. UI must observe JobManager state; widgets must not own worker process lifecycle.
3. Support multiple concurrent logical jobs and deterministic ordering/history retention.
4. Expose hooks for future reconstruction/subprocess adapters without starting M07.
5. Add tests for state transitions, progress monotonicity, concurrency ordering, failure details and bounded history.

## Validation

Use PySide6 offscreen/headless tests where practical. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Any dependency change must update pyproject.toml and uv.lock reproducibly. Create one implementation/evidence commit and a separate log-only commit. User-facing repository links must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
