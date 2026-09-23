# PL-0085 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `158ff752075c2cd8c7af2053a8071673539e69cb`

## Independent result

The remediation removes the original hard-coded unavailable overlay:
- the root view owns a runtime view model;
- initial tracking snapshot and latest AR pose come from the shared ARTrackingService;
- overlay formatting supports pose, orientation, motion and unavailable labels;
- simulator behavior remains truthful.

The “live shared state” requirement is still incomplete.

### 1. Runtime values are sampled only once

`CaptureRuntimeViewModel.start()` performs one:
- `trackingService.snapshot()`;
- `trackingService.latestPose()`.

There is no update stream, polling loop, observation callback or AR-frame subscription that updates `tracking` / `pose` after startup.

The overlay therefore displays a startup snapshot, not live pose/tracking state.

### 2. Localization epoch is permanently zero in the runtime model

`@Published private(set) var epoch = 0` is never updated from `SharedARSessionOwner.epochCoordinator`.

The overlay's epoch line is therefore still a placeholder value rather than the current localization epoch.

### 3. Motion is never populated

`@Published private(set) var motion: MotionSampleRecord?` exists, but final `ContentView` does not own/start a MotionService and never assigns `motion`.

The overlay always renders `Motion: unavailable` in the actual app regardless of physical CoreMotion availability.

### 4. Tests cover formatting, not live view-model behavior

The new test manually passes a pose/motion into `PoseOverlayModel`.

It does not prove that `CaptureRuntimeViewModel` receives ongoing AR/motion/epoch changes.

## Criteria

- PASS: 1-9, 12-13, 15-18
- FAIL: 10, 11, 14, 19

## Required remediation

1. Continuously update the runtime model from the shared AR service/owner without creating a second sensor pipeline.
2. Publish the real localization epoch into the runtime model.
3. Feed the one canonical MotionService's current motion record into the overlay.
4. Add view-model integration tests proving values change after startup and unavailable/simulator states remain truthful.

PL-0085 remains unchecked.

Decision: **CHANGES_REQUIRED**
