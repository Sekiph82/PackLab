# PL-0092 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `4f45c52bb4599b1f73810fce3eed9f7a859c30d8`
Remediation log: `PL-0092_CODEX_LOG_V02.md`

## Independent result

The remediation adds:
- real session-directory enumeration;
- draft metadata decoding;
- a SwiftUI history view;
- preview-derivative display;
- visible degraded rows for corrupt metadata or missing previews;
- deterministic sorting.

The authoritative finalization/history contract is still incomplete.

### Finalization state source is not produced by the real finalization workflow

`LocalScanHistoryStore` reads `finalization.json` and treats it as the authoritative export state.

The inspected PL-0091 finalization implementation does not write `SessionFinalizationRecord` / `finalization.json`. Therefore the history store's exported/finalized state source is disconnected from the actual finalization path and will normally remain `in_progress` unless another caller manually writes that file.

### Corrupt finalization record is silently treated as no finalization

If `finalization.json` exists but fails decoding, the code converts it to nil and presents `in_progress`. A corrupt authoritative record should produce a degraded/corrupt state, not silently downgrade to “not finalized”.

### Frozen state-transition/corrupt-record tests are missing

The added test covers one missing-preview case. It does not cover:
- finalized/exported state produced by the actual finalizer;
- transition from in-progress to finalized/exported;
- corrupt finalization record;
- corrupt metadata record;
- deterministic ordering across multiple sessions.

## Required remediation

1. Make PL-0091 finalization persist the authoritative finalization state that PL-0092 reads, or derive history directly from another authoritative artifact.
2. Treat a present-but-corrupt finalization record as degraded/corrupt, not in-progress.
3. Add tests for in-progress → finalized/exported transition, corrupt finalization, corrupt metadata, missing preview and multi-entry ordering.
4. Keep history UI preview-only and retain degraded rows.

PL-0092 remains unchecked.

Decision: **CHANGES_REQUIRED**
