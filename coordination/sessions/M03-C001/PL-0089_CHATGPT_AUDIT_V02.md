# PL-0089 — ChatGPT Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `a9eb235a129d6455aec2cb1d756615c49431fa26`
Remediation log: `PL-0089_CODEX_LOG_V02.md`

## Independent result

The remediation adds:
- a real `SessionGalleryStore`;
- a SwiftUI gallery list;
- preview-only display;
- degraded status for missing preview/source;
- delete/retake audit events.

Material integration defects remain.

### Gallery record decoding conflicts with PL-0088 persistence

`SessionGalleryStore.load()` decodes every record JSON as `AcceptedCaptureRecord`.

PL-0088 `storeAcceptedCapture` writes arbitrary photo metadata bytes into that record path. The provided remediation test itself stores `Data("{}")` as metadata and then expects `gallery.load()` to succeed. That expectation is inconsistent with the implementation and would decode-fail.

### Delete/retake are not exposed in the actual gallery UI

`AcceptedFrameGalleryView` only displays rows. It has no delete or retake controls, no confirmation UI, and no mutation callback path. The frozen task is an accepted-frame gallery **with delete/retake controls**, not only a backing actor API.

### Session state/index is not updated coherently

`delete` removes files and appends an audit event, but does not update `PersistedSessionState.acceptedIDs`, sequence state, replacement trace, or other authoritative session state.

`retake` writes new source/record bytes and an audit event, but likewise does not update persisted accepted IDs/sequence/replacement state. It also writes caller `metadata` to a path the loader expects to contain `AcceptedCaptureRecord`.

## Required remediation

1. Resolve the canonical per-photo record contract with PL-0088.
2. Add real delete and retake controls to the SwiftUI gallery, including confirmation/error states.
3. Make delete/retake update authoritative persisted session state atomically with files/audit history.
4. Add tests for actual persisted ordering, delete, retake, missing preview, missing source and corrupt record behavior.

PL-0089 remains unchecked.

Decision: **CHANGES_REQUIRED**
