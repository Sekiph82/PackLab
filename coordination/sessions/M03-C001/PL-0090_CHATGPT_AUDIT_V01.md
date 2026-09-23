# PL-0090 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `a0d1ab832476464903b413960bb9ae3c89ae4502`

## Independent findings

The child adds a useful pure validator:
- persisted session ID/version/next-sequence/epoch/accepted IDs;
- missing-state/version/sequence/missing-source blocking;
- deterministic resumable versus blocked disposition.

The actual app-termination resume workflow is not implemented.

### No launch-time session discovery or resume UI

There is no code that scans the PackLab session root on app launch, identifies incomplete sessions, or presents Resume / Discard / navigation choices. `discardRequired` is declared but never used.

### No persisted-file reconstruction

The validator accepts an already-constructed `PersistedSessionState` and a set of source IDs. It does not reopen `metadata.json`, `state.json`, per-photo records or source files from `ScanSessionStore`, validate stale temp files, and reconstruct the active session model.

### Required history is incomplete

The state carries accepted IDs and epoch, but no rejected-frame history/replacement history or other capture-session state required by criterion 12.

### Frozen restart/crash tests are missing

Criterion 14 requires clean termination, simulated crash, missing file, stale temp file and version mismatch. The inspected tests cover only:
- valid in-memory state;
- nil state;
- version mismatch.

No filesystem restart, crash, stale-temp or missing-file recovery test exists.

## Criteria

- PASS: 1-9, 16-18
- FAIL: 10, 11, 12, 13, 14, 15, 19-20

## Required remediation

1. Discover incomplete sessions from the canonical session store on app launch.
2. Reopen and validate persisted metadata/state/per-photo/source records, including stale-temp/incomplete-write handling.
3. Reconstruct sequence, accepted/rejected/replacement history and localization epoch into one resumable session model.
4. Add visible deterministic Resume / Discard / blocked-corrupt workflow.
5. Add filesystem restart tests for clean termination, simulated crash, missing record/source, stale temp and version mismatch.
6. Publish a complete task-specific log checkpoint.

PL-0090 remains unchecked.

Decision: **CHANGES_REQUIRED**
