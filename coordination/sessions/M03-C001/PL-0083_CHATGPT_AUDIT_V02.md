# PL-0083 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `0d055ea33cf4bdb6e8b41aac465fab8df4667cf3`

## Independent result

The remediation adds a sound pure policy:
- configurable stable-normal-frame hysteresis;
- recovering state before pose eligibility returns;
- retained diagnostic events;
- a warning view-model projection;
- deterministic flapping/stability tests.

The mandatory real-app integration is absent.

### 1. TrackingRecoveryPolicy is not used by the capture runtime

Final `ContentView.CaptureRuntimeViewModel` directly assigns:

`tracking = await trackingService.snapshot()`

It does not own or update a `TrackingRecoveryPolicy`.

Therefore the real UI can still transition directly from degraded to normal based on the underlying service snapshot without the remediation hysteresis.

### 2. TrackingWarningViewModel is not used by SwiftUI

The visible tracking message in `ContentView` is driven directly from:

`runtime.tracking.poseEvidenceEligible` and `runtime.tracking.message`.

No inspected UI/view-model path constructs or consumes `TrackingWarningViewModel`.

### 3. Tracking is not updated live after startup

`CaptureRuntimeViewModel.start()` starts the service and takes one tracking snapshot. There is no AR tracking update stream/poll loop that feeds subsequent limited/recovering/normal changes into the runtime UI.

Thus even the underlying non-hysteretic warning is not a live AR degradation surface.

### 4. Diagnostic retention remains only inside an unused pure struct

`TrackingRecoveryPolicy.diagnostics` is in-memory state on the unused policy instance. It is not connected to the app diagnostics retention/export path.

## Criteria

- PASS: 1-9, 11, 13, 15-18
- FAIL: 10, 12, 14, 19

## Required remediation

1. Integrate one TrackingRecoveryPolicy into the actual tracking runtime/view model.
2. Feed real AR tracking updates continuously into it.
3. Drive the visible warning from the hysteresis-controlled snapshot.
4. Retain degradation events through the project diagnostics/session evidence path.
5. Add integration tests proving real view-model warning does not clear until the stable-normal threshold.

PL-0083 remains unchecked.

Decision: **CHANGES_REQUIRED**
