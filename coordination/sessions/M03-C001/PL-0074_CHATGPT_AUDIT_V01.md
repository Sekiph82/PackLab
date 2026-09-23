# PL-0074 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `1b184c97ca31f7bfc0de5b48eccf94f421f91b1a`

## Independent findings

The child correctly adds:
- exposure states/capabilities;
- bias clamping against declared and AVFoundation device limits;
- continuous-auto metering;
- an optional AVFoundation lock path;
- deterministic policy tests for clamping and lock gating.

Mandatory integration is still incomplete.

### Exposure state is not persisted into capture-ready/per-photo state

The frozen requirement says the exposure mode/state used for each capture-ready state must be recorded. The inspected child only returns an `ExposureState` from the policy/adapter. It does not bind that state to the camera/capture session or the accepted-still metadata path.

### Unsupported lock is not visibly surfaced

There is no UI/view-model integration showing lock availability/unavailability. The pure policy can return `.failed`, but this is not the required visible user state.

### Existing serialized configuration coordinator is bypassed

`AVFoundationExposureAdapter.configure` calls `device.lockForConfiguration()` directly. It does not execute through the existing `CameraConfigurationCoordinator` introduced to serialize camera configuration changes. Therefore criterion 13 / Requirement D is not satisfied by the real adapter path.

## Criteria

- PASS: 1-11, 14-18
- FAIL: 12, 13, 15, 19-20

## Required remediation

1. Route exposure configuration through the shared serialized camera configuration coordinator/session ownership path.
2. Integrate exposure state with the selected main camera and capture-ready state.
3. Persist the actual exposure mode/state into the per-photo metadata flow when a still is accepted.
4. Surface metering/locked/unavailable/failure state in the capture UI or its view model.
5. Add behavior-bearing tests for serialized configuration, unsupported lock visibility/state, and capture metadata binding.
6. Publish a complete task-specific log checkpoint.

PL-0074 remains unchecked.

Decision: **CHANGES_REQUIRED**
