# PL-0142 — Codex Work Order V01

Task: **PL-0142 — Version/update information screen**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0142_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0142_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0142_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

M06 project state must preserve M05 raw-ingest authority and keep UI separate from project/domain services.

## Mandatory implementation

1. Add an About/Version screen showing PackLab Studio version, Python version, Qt/PySide6 version, PackScan schema support and build/revision metadata when available.
2. Show update information only from local/static build metadata or a manually supplied release manifest; no online service is required.
3. Distinguish current version, available-local-manifest version, unsupported/malformed manifest and no-manifest states.
4. Do not implement auto-download/install in M06.
5. Add tests for version rendering, local manifest comparison, malformed manifest, no-network requirement and privacy-safe output.

## Validation

Use deterministic filesystem/offscreen UI tests. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Update declared/locked dependencies reproducibly if needed. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
