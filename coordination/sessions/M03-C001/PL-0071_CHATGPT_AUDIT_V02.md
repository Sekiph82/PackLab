# PL-0071 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `46f7f8afde0c3263b7b4bc3fbd9b72f0f0c6eb6c`

## Independent result

The remediation successfully replaces the previous placeholder with a real NextLevel photo delegate path:
- high-resolution photo capture is enabled;
- `capturePhoto()` is invoked;
- `AVCapturePhoto.fileDataRepresentation()` and resolved pixel dimensions are returned;
- duplicate continuation completion is guarded;
- cancellation and missing-data failures are explicit.

Material remediation requirements remain open.

### 1. Deterministically selected main rear lens is still not bound to still capture

The final `NextLevelStillCaptureAdapter` stores only `NextLevel` (default `.shared`). It does not accept or verify the PL-0070 `CameraLensIdentity`, nor does it configure/validate that the active NextLevel session/device is the deterministically selected rear wide camera.

The selection model exists elsewhere, but no inspected connection guarantees this still is captured by that selected lens.

### 2. Session-stop cleanup is not implemented

The adapter cleans up on delegate completion and task cancellation, but exposes no session-stop/interruption hook that fails and clears an outstanding continuation when the camera session is stopped/restarted externally.

This leaves the frozen criterion's explicit “session-stop cleanup” requirement incomplete.

### 3. Added test does not exercise the real delegate/backend seam

The new XCTest validates only the standalone `StillCaptureLifecycle` struct. That struct is not used by `NextLevelStillCaptureAdapter`.

There is no injected NextLevel/delegate/backend harness testing:
- delegate success;
- missing data/dimensions;
- duplicate callback;
- cancellation;
- session stop;
- selected-lens binding.

## Criteria

- PASS: 1-10, 13, 15-18
- FAIL: 11, 12, 14, 19

## Required remediation

1. Bind the still adapter/session to the PL-0070 selected rear-wide device and fail closed if the active device does not match.
2. Add an explicit camera-session stop/interruption cleanup hook for an in-flight still.
3. Test the actual adapter/delegate seam through an injectable capture driver rather than only a disconnected lifecycle struct.
4. Cover success, duplicate callback, cancellation, unavailable capture, missing data, session stop and selected-lens mismatch.

PL-0071 remains unchecked.

Decision: **CHANGES_REQUIRED**
