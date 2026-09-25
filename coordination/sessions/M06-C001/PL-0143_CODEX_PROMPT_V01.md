# PL-0143 — Codex Work Order V01

Task: **PL-0143 — PackLab project directory layout**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0143_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0143_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0143_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

M06 project state must preserve M05 raw-ingest authority and keep UI separate from project/domain services.

## Mandatory implementation

1. Define a versioned PackLab project layout separating raw, working, derived, cache/temp and export data plus project metadata/history/recovery state.
2. Raw must remain immutable-by-policy and compatible with accepted M05 raw-ingest evidence; working/derived/export must never overwrite raw authority.
3. Define canonical path helpers, safe relative-path rules, directory creation/validation and schema versioning.
4. Document which later milestones own each area and which files are portable versus regenerable.
5. Add filesystem tests for creation, validation, traversal rejection, existing layout reuse and corrupt/incompatible layout detection.

## Validation

Use deterministic filesystem/offscreen UI tests. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Update declared/locked dependencies reproducibly if needed. Create one implementation/evidence commit and one separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
