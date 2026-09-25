# PL-0119 — Codex Work Order V01

Task: **PL-0119 — .packscan finalization with checksums and atomic rename**

Repository: https://github.com/Sekiph82/PackLab
Master batch: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
This prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CHATGPT_AUDIT_CRITERIA_V01.md
Required log: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0119_CODEX_LOG_V01.md

## Authorization

TASKS.md must authorize `M05-BATCH-001 / READY / CODEX`. M03 and M04 must remain accepted. PL-0068 remains unchecked / OWNER_REQUIRED. Never edit TASKS.md or ChatGPT audit artifacts. Never start M06.

Reuse the accepted M02 PackScan contracts and M03/M04 session/finalization architecture. Do not create parallel package writers, camera/session owners or mutable export formats.

## Mandatory implementation

1. Reuse the accepted PackScanWriter/SessionFinalizer contracts; do not create a second container writer.
2. Finalize only from authoritative accepted-session records and immutable source bytes into one `.packscan` file.
3. Ensure manifest payload declarations, per-payload SHA-256, checksums.json coverage, deterministic ZIP layout, and canonical schema version remain valid.
4. Publish through a same-filesystem temporary file plus atomic rename/move; never expose a partial final package at the destination.
5. On any validation/write/rename failure, keep the scan resumable, clean temporary artifacts, and do not mark export/finalization complete.
6. Add real filesystem tests for success, destination exists, checksum mismatch, missing source, write/rename failure, and no-partial-file guarantees.

## Validation

Add behavior-bearing success, failure, cancellation, restart and exact-boundary tests appropriate to the task. Run focused tests, the full declared locked suite, relevant iOS/static/project checks, `git diff --check`, protected-file checks, and privacy/signing/secret review. Native iPhone/Xcode/network hardware claims may be made only if genuinely executed.

Create one implementation/evidence commit and then a separate child log-only commit. Every user-facing repository link must be a full GitHub URL, never a local filesystem path.

End the child log exactly:

`READY_FOR_INDEPENDENT_AUDIT`
