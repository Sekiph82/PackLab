# PL-0081 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `68da95dd0ccfd5c7c54a4344cce73f6bb37a8dde`

## Independent findings

The child materially adds:
- a real `CMMotionManager` device-motion source;
- a fixed 60 Hz update cadence;
- CoreMotion monotonic timestamps;
- quaternion attitude and rotation-rate capture;
- bounded motion buffering;
- nearest-sample tolerance logic;
- deterministic bounded/stale tests.

However mandatory integration remains incomplete.

### Existing MotionService seam is bypassed

M01 already defines the project `MotionService` abstraction and simulator fallback. The new `CoreMotionController` is a separate concrete API and does not implement/adapt the existing service. Physical and simulator behavior therefore live behind different ownership paths.

### No accepted-capture alignment binding

`MotionBuffer.nearest` exists, but no capture pipeline invokes it for each accepted still/capture timestamp and no aligned motion record is persisted. Criterion 12 / Requirement C is not implemented end-to-end.

### Unavailable/error behavior is silent

If `isDeviceMotionAvailable` is false, `start()` simply returns. The completion handler ignores its error parameter. There is no explicit unavailable/failure state exposed through the service contract, which is required by criterion 13.

## Criteria

- PASS: 1-7, 9-11, 14, 16-18
- FAIL: 8, 12, 13, 15, 19-20

## Required remediation

1. Put the CoreMotion implementation behind the existing `MotionService` seam and preserve the simulator no-evidence implementation under the same contract.
2. Represent unavailable/start/update errors explicitly rather than silently returning/ignoring errors.
3. Bind the nearest eligible motion sample to each accepted capture timestamp and persist the alignment delta/status.
4. Keep buffering bounded and document the CoreMotion timestamp basis relative to capture timing.
5. Add deterministic integration tests for accepted-capture alignment, stale/missing data and provider failure.
6. Publish a complete task-specific log checkpoint.

PL-0081 remains unchecked.

Decision: **CHANGES_REQUIRED**
