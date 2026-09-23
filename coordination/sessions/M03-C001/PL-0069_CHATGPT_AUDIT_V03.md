# PL-0069 — ChatGPT Independent Remediation Audit V03

Decision: **CHANGES_REQUIRED**

Implementation commit: `6844ea6c374cf0573a65831a0ef3d72039eb4185`
Remediation log: `PL-0069_CODEX_LOG_V03.md`

## Independent findings

The remediation materially improves the previous implementation:
- preview layer is reattached on reappearance;
- attach/detach counters are now idempotent;
- denied/restricted/unavailable authorization states are visibly surfaced;
- the narrow UIKit bridge is preserved.

Two mandatory remediation criteria remain open.

### 1. Authorization is checked after the lifecycle is marked started

`viewDidAppear` executes:

`guard lifecycle.startIfNeeded() else { return }`

before checking `AVCaptureDevice.authorizationStatus(for: .video)`.

If the first appearance is denied/restricted/not-determined-and-denied, `startIfNeeded()` has already marked the lifecycle started even though the camera session never started. A later appearance after the user enables camera access can hit `startIfNeeded() == false` and return before `startAuthorizedPreview()`.

The lifecycle start state therefore does not truthfully represent whether NextLevel actually started, and permission recovery can be blocked.

### 2. Required behavior-bearing remediation tests were not added

The remediation criteria explicitly require tests for:
- authorization/error mapping;
- disappear → reappear attach/start/stop transitions.

The implementation commit changes only `CameraFoundation.swift` and `CameraService.swift`; no XCTest file changed. The child log says existing tests remain, but the frozen remediation criterion requires new/updated behavior-bearing coverage of the repaired paths.

### 3. Real NextLevel session failure propagation is still not demonstrated

Authorization failures are handled, but the inspected physical preview controller still has no NextLevel/session error callback path feeding `PreviewSurfaceState.error` / `.unavailable`. The new `PreviewAuthorizationResolver.state(for: CameraServiceError)` is not connected to a NextLevel delegate/session failure source.

## Criteria

- PASS: 1-9, 11-12, 15-18
- FAIL: 10, 13, 14, 19

## Required remediation

1. Do not mark preview lifecycle started until authorization succeeds and the real preview/session start path is entered successfully.
2. Ensure permission denial followed by later authorization can recover on a subsequent appearance.
3. Wire actual NextLevel/session runtime/start failure callbacks into the visible preview state path.
4. Add behavior-bearing tests covering denied/restricted/error mapping and repeated appear/disappear/permission-recovery lifecycle behavior.

PL-0069 remains unchecked.

Decision: **CHANGES_REQUIRED**
