# PL-0140 — Codex Work Order V01

Task: **PL-0140 — Cancellation and safe shutdown**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0140_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. M03–M05 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M07.

M06 hosts existing M05 Windows services; do not duplicate ingest, validation, quarantine, raw-store, receiver or transfer logic.

## Mandatory implementation

1. Integrate JobManager with the existing safe packlab_core.subprocess_runner cancellation semantics rather than inventing a second process-kill implementation.
2. On app close, detect active jobs and execute a bounded cancellation/shutdown policy that stops only PackLab-owned subprocess trees.
3. Do not block the GUI thread indefinitely; expose shutdown progress/state and a deterministic terminal result.
4. Preserve structured cleanup errors and do not silently claim cancellation succeeded if cleanup failed.
5. Add tests for idle close, active cancellable job, multiple jobs, cleanup failure, bounded timeout and no unrelated-process termination.

## Validation

Use PySide6 offscreen/headless tests where practical. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Any dependency change must update pyproject.toml and uv.lock reproducibly. Create one implementation/evidence commit and a separate log-only commit. User-facing repository links must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
