# PL-0071 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `ec3b045b5dea2a5ae7f33fedb58a131da43238b8`

## Independent finding

The child adds useful framework-independent foundations:
- `CaptureDimensions`;
- immutable `AcceptedStill`;
- explicit accepted/rejected result;
- actor-isolated single-flight gate;
- injected `StillPhotoBackend`;
- deterministic overlap/invalid-source behavior.

Those seams are valuable, but the frozen task was to **implement high-resolution still-photo capture through the selected main camera**.

The inspected physical adapter does not do that. `NextLevelStillCaptureAdapter.requestOriginalStill()` contains only a comment about the NextLevel photo delegate and then immediately:

`throw CameraServiceError.unavailable`

Therefore there is no real NextLevel still request, no delegate/continuation completion path, no delivery of source bytes from the selected main camera, and no evidence that a device build could execute the required capture behavior.

The Codex log itself acknowledges that native photo delegate execution remains a future/device-side follow-up. That is incompatible with criteria 9 and 10, which require the implementation itself rather than a placeholder seam.

## Criteria

- PASS: 1-8, 11-14, 16-19
- FAIL: 9, 10, 15, 20

## Required remediation

1. Implement the real NextLevel high-resolution photo request/delegate handoff behind `StillPhotoBackend`.
2. Bind capture to the deterministically selected main rear lens/session architecture.
3. Resume exactly once per capture request and clean up delegate/continuation state on success, failure, cancellation and session stop.
4. Preserve original image bytes and dimensions without resize/crop/recompression shortcuts.
5. Add behavior-bearing tests for success, failure, duplicate callback and overlapping request handling using an injected delegate/backend seam.

PL-0071 remains unchecked.

Decision: **CHANGES_REQUIRED**
