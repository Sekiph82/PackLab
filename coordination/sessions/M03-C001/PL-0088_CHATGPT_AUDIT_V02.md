# PL-0088 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `62e6e9d4ca798ba62f909f0f5ba20ff5c8b5135a`
Remediation log: `PL-0088_CODEX_LOG_V02.md`

## Independent result

The remediation adds useful real filesystem behavior:
- a dedicated records directory;
- stale-temp cleanup;
- duplicate capture rejection;
- a reopen path;
- an accepted-capture persistence API.

Two material defects remain.

### Accepted-capture write is not crash-atomic

`storeAcceptedCapture` writes the source directly to its final image path, then writes the record, then replaces session state. Synchronous errors can be rolled back, but a process/app crash between those operations can leave an orphan source, orphan record, or old state.

That does not satisfy the frozen crash-safe transaction requirement. A true crash-safe transaction needs staged files/transaction marker or equivalent recovery semantics that can deterministically complete or roll back after restart.

### Per-photo record format is inconsistent with downstream gallery loading

`storeAcceptedCapture(source:record:metadata:state:)` writes the caller-provided `metadata` bytes into `records/<metadataFilename>`.

The downstream `SessionGalleryStore.load()` decodes those files as `AcceptedCaptureRecord`. Those are different contracts. The remediation test writes `Data("{}")` as metadata, which cannot decode as `AcceptedCaptureRecord`.

This means the storage and gallery layers are internally inconsistent on final main.

### Required failure-injection coverage is still incomplete

The new test covers stale-temp cleanup and duplicate capture, but not:
- simulated interruption/crash between source, record and state stages;
- corrupt/incomplete transaction recovery;
- missing/corrupt record on reopen.

## Required remediation

1. Define one canonical per-photo persisted record format used consistently by storage/gallery/resume.
2. Make accepted-capture persistence crash-recoverable as a transaction, not only exception-rollback safe.
3. Add restart recovery for every partial transaction stage.
4. Add filesystem failure-injection tests for interrupted source/record/state writes and corrupt/incomplete reopen.

PL-0088 remains unchecked.

Decision: **CHANGES_REQUIRED**
