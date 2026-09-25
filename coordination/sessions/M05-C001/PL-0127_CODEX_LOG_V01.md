# PL-0127 — Codex Implementation Log V01

- Task: PL-0127 — Windows drag/drop and file-picker ingest entry points
- Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CODEX_PROMPT_V01.md
- Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/PL-0127_CHATGPT_AUDIT_CRITERIA_V01.md
- Master prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M05-C001/MASTER_CODEX_PROMPT_V01.md
- Starting synchronized commit: `eaebf6124fc394694d96023c87996f30627259fe`
- Implementation commit: `3088ee4a643d8c68d0f63bc7c44ba564c9f3613d`

## Authorization and synchronization

M05-BATCH-001 / READY / CODEX remained live; M03/M04 remained accepted, PL-0068 remained OWNER_REQUIRED, and M06 remained unstarted. The checkout was clean after PL-0126 publication. Root `TASKS.md` and ChatGPT audit files were untouched.

## Files changed

- `apps/windows-studio/src/packlab_studio/ingest.py`
- `tests/transfer/test_ingest_controller.py`

`IngestController` exposes deterministic drop and picker adapters converging on one `ImportService`. The service normalizes Windows paths, accepts only regular `.packscan` files, validates through the existing PackScan authority, and returns structured validated/rejected/cancelled results. Duplicate selections, unsupported extensions, directories, missing paths, corrupt packages and picker cancellation are deterministic. No PySide6 shell was introduced.

## Validation evidence

Command: `uv run pytest -q tests/transfer tests/tools tests/packscan`

- Expected: valid drop/picker, ordering, duplicate, path rejection and existing transfer/PackScan/project tests pass.
- Actual: `97 passed, 1 warning`.

Command: `uv run ruff check apps/windows-studio/src/packlab_studio/ingest.py tests/transfer/test_ingest_controller.py`

- Actual: passed.

Command: `git diff --check`

- Actual: passed.

The service returns `validated`, not imported, until later children add raw/quarantine/index/report publication. No invalid package is extracted or promoted. Protected tracker/audit files were unchanged.

## Security and scope

Only package names, capture IDs and non-secret whole-file digests are returned. Absolute private paths are not placed in result content. No credentials, private scans, signing material, caches or M06 UI were added.

## Publication

The implementation commit is followed by a separate log-only publication commit; remote visibility is verified before PL-0128 begins.

READY_FOR_INDEPENDENT_AUDIT
