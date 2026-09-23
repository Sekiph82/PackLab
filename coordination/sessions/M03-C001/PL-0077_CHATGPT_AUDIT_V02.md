# PL-0077 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `affd82ae5df95eecb53580349f7ccd43c66474a2`

## Independent result

The remediation adds real AVFoundation session notification ownership:
- interruption/interruption-ended/runtime-error notifications are registered idempotently;
- observer tokens are removed on unregister;
- NextLevel start errors are now caught;
- a recovery owner exposes state-change and in-flight cancellation seams;
- the pure integration model demonstrates accepted IDs surviving an interruption.

The real product integration is still incomplete.

### 1. In-flight cancellation seam is never connected to real still capture

Final `main` defines `CameraRecoveryOwner.setInFlightCancellation`, but no inspected caller invokes it.

Therefore an actual NextLevel still request is not cancelled/failed by the recovery owner when interruption/runtime-error notifications arrive.

The pure `CameraRecoveryIntegrationModel` does not close this real adapter gap.

### 2. Permission signals are not wired into CameraRecoveryOwner

The preview controller checks AVFoundation authorization and updates its status label, but it does not call `recoveryOwner.handle(.permission(...))` for denied/restricted/authorized states.

Thus the “actual permission signal” requirement remains split across two parallel state paths.

### 3. Interruption-ended does not perform recovery/restart

`handle(.interruptionEnded)` only advances the state machine to `.restarting`.

No inspected code attempts to restart NextLevel/the AVCaptureSession, applies bounded retries, or emits `.restartSucceeded` / `.restartFailed`.

So the implementation observes recovery events but does not execute recovery.

### 4. Recovery state/messages are not bound to the actual UI/view model

`onStateChange` exists but is never assigned in final `main`.

The preview's visible status path is still manually driven separately. There is no shared user-facing recovery model.

### 5. Integration test does not exercise notification owner/adapters

The added test covers only `CameraRecoveryIntegrationModel`, not injected NotificationCenter registration, duplicate listener behavior, actual cancellation callback, or restart success/failure.

## Criteria

- PASS: 1-9, 11, 15-18
- FAIL: 10, 12, 13, 14, 19

## Required remediation

1. Connect recovery cancellation to the real in-flight NextLevel still adapter/service.
2. Route actual camera authorization outcomes through the same recovery owner.
3. Implement bounded restart execution after recoverable interruption/runtime failures.
4. Bind recovery state/message into the actual capture UI/view model.
5. Add injected NotificationCenter/session tests for idempotent observers, cancellation callback, restart success/failure and permission transitions.

PL-0077 remains unchecked.

Decision: **CHANGES_REQUIRED**
