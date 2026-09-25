# PL-0127 — Codex Work Order V01

Task: **PL-0127 — Windows drag/drop and file-picker ingest entry points**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03/M04 remain accepted. PL-0068 remains OWNER_REQUIRED. Never edit TASKS.md/ChatGPT audits. Never start M06.

Reuse `packlab_core.packscan` as the package validation authority and keep the Windows receiver/import layer headless/testable so M06 can later provide the full PySide6 shell without rewriting ingest logic.

## Mandatory implementation

1. Create a PackLab Studio ingest application/controller boundary for `.packscan` paths that will later plug into the M06 PySide6 shell without starting M06 now.
2. Expose both dropped-path intake and file-picker-selected-path intake through the same authoritative import service; do not duplicate validation/import logic.
3. Accept only `.packscan` files, reject directories/multiple unsupported types deterministically, and normalize Windows paths safely without modifying the source.
4. Provide a minimal Windows-native/file-picker adapter seam and deterministic test fake so the flow is executable/testable now and visually wireable by M06 later.
5. Return structured import results/errors suitable for Capture Inbox UI rather than printing ad-hoc text.
6. Add tests for valid selected file, valid dropped file, multiple drop ordering, unsupported extension, directory, missing path and duplicate selection.

## Validation

Add behavior-bearing filesystem/network/application tests for success, failure, restart, corruption and exact conflict cases. Run focused tests, the full declared locked suite, Ruff/project/static checks, `git diff --check`, protected-file and privacy/secret checks. Do not claim physical iPhone/Windows LAN validation unless actually executed.

Create one implementation/evidence commit and a separate child log-only commit. User-facing repository links must be full GitHub URLs only.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
