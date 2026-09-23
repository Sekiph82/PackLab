# PL-0092 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `16fffc6c696e0f51c7b133337dacf4cc9de87ed3`

## Independent findings

The child adds useful presentation/index primitives:
- stable history entry fields for ID/name/type/date/preview/export state;
- deterministic date + ID sorting;
- an explicit degraded-entry representation;
- a simple ordering/degraded test.

The frozen local-history workflow is not implemented end-to-end.

### History is not derived from authoritative records

`ScanHistoryIndex` accepts already-created `ScanHistoryEntry` values. No code enumerates `ScanSessionStore` / finalized .packscan records and derives the entry fields from authoritative session/finalization state. The Codex log's statement that entries are “derived from session/finalization records” is not supported by the implementation diff.

### No local scan history UI

No SwiftUI history screen/list is added, so the app does not actually show previews, dates, package types or export states.

### Missing/corrupt data is not detected

`degraded(id:reason:)` can create a degraded entry only after a caller has already decided something is corrupt. There is no loader that detects:
- missing preview;
- corrupt session metadata;
- corrupt finalization record;
- missing source/reference.

### Frozen tests are incomplete

Criterion 14 requires tests for:
- ordering;
- state changes;
- missing preview;
- corrupt entry handling.

The inspected test covers ordering and a manually-created degraded entry only. It does not test state updates or automatic missing-preview/corrupt-record handling.

## Criteria

- PASS: 1-9, 13, 16-18
- FAIL: 10, 11, 12, 14, 15, 19-20

## Required remediation

1. Build history entries by enumerating/validating authoritative local session and finalization records.
2. Add the actual SwiftUI local scan history screen using preview derivatives only, not full-resolution source images.
3. Detect missing/corrupt preview/record data and preserve a visible degraded entry rather than hiding it.
4. Define/update export/finalization state deterministically from authoritative records.
5. Add tests for ordering, state transitions, missing preview, corrupt metadata/finalization records and degraded-entry retention.
6. Publish a complete task-specific log checkpoint.

PL-0092 remains unchecked.

Decision: **CHANGES_REQUIRED**
