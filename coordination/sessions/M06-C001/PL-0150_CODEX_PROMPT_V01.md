# PL-0150 — Codex Work Order V01

Task: **PL-0150 — Project portability check**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M06-C001/PL-0150_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M06-BATCH-001 / READY / CODEX`. Preserve accepted M03–M05 and PL-0068 OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M07.

For PL-0151/0152, use measured local evidence and a single viewport adapter boundary. Do not hard-code the rest of Studio to an experimental backend before the spike decision is frozen.

## Mandatory implementation

1. Implement a portability scanner that identifies external/non-project asset references, missing required files, absolute/private paths and non-portable links.
2. Classify findings as required-missing, external-but-present, regenerable cache/derived, and portable project-owned data.
3. Offer a report/plan only in M06; do not silently copy or rewrite external assets.
4. Ensure raw evidence/project metadata/history integrity is checked without leaking user absolute paths in portable report output.
5. Add tests for fully portable project, missing external asset, present external asset, symlink/path traversal, regenerable derived data and redacted report.

## Validation

Use deterministic filesystem/offscreen tests and reproducible benchmark commands. Run focused tests, exact full locked suite, Ruff, mypy/static/project checks, compileall and `git diff --check`. Declare/lock any viewport dependency and record license impact. Create one implementation/evidence commit and separate log-only commit. User-facing repository references must be full GitHub URLs.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`
