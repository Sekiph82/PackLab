# PL-0138 — Codex Work Order V01

Task: **PL-0138 — Persistent window/workspace preferences**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0138_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. M03–M05 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M07.

M06 hosts existing M05 Windows services; do not duplicate ingest, validation, quarantine, raw-store, receiver or transfer logic.

## Mandatory implementation

1. Persist window geometry, maximized/fullscreen state, dock layout, last route, theme/display preferences and other M06 UI preferences using a versioned settings schema.
2. Use Qt settings or an owned JSON/settings adapter with atomic/versioned migration behavior; never persist private project payloads or secrets in UI preferences.
3. Restore safely after invalid/corrupt/older preference state and fall back to a usable default layout.
4. Keep settings injectable for tests and portable across normal Windows user profiles.
5. Add tests for round-trip, corrupt state, version migration/defaulting, off-screen/invalid geometry sanitization and reset.

## Validation

Use PySide6 offscreen/headless tests where practical. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Any dependency change must update pyproject.toml and uv.lock reproducibly. Create one implementation/evidence commit and a separate log-only commit. User-facing repository links must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
