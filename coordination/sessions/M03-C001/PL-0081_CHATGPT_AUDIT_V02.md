# PL-0081 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `8250f576e077565fed9f706eec6fa1f638f8e380`

## Independent result

The remediation improves the common service contract:
- `MotionServiceState` exposes idle/running/unavailable/failed;
- a physical CoreMotion service exists behind `MotionService`;
- simulator remains explicitly unavailable;
- motion-record validation and bounded alignment models are stronger.

The previous integration gap is not actually closed.

### 1. Two independent CoreMotion pipelines still exist

Final `main` still contains the old `TrackingFoundation.CoreMotionController`, which owns its own `CMMotionManager` and fills `MotionBuffer` with attitude quaternion + rotation rate.

The new `CoreMotionMotionService` owns a second `CMMotionManager`.

So physical CoreMotion evidence is still split across parallel owners instead of one service-backed pipeline.

### 2. MotionService does not provide the required attitude/rotation-rate records

`CoreMotionMotionService.latestSample()` stores only user-acceleration X/Y/Z in `MotionSample`.

The required attitude/orientation quaternion and rotation rate are still produced only by the separate legacy `CoreMotionController`.

Thus putting the physical implementation “behind MotionService” did not move the actual PL-0081 evidence stream behind that seam.

### 3. Accepted-capture alignment is not connected to the service

`MotionAligner.bind(... buffer: MotionBuffer)` operates on a buffer owned by the separate controller/model.

No inspected path connects `CoreMotionMotionService` updates to that buffer or invokes MotionAligner automatically when a still is accepted.

As with PL-0080, accepted stills also currently carry a wall-clock `Date` rather than a monotonic capture timestamp, so the actual timestamp-domain binding remains unresolved.

### 4. Tests do not cover provider failure/service integration

The added test exercises a manually populated `MotionBuffer`.

It does not test:
- MotionService unavailable/failure mapping;
- one-owner CoreMotion updates;
- attitude/rotation-rate data through the service seam;
- accepted-still alignment;
- exact tolerance boundaries.

## Criteria

- PASS: 1-11, 15-18
- FAIL: 12, 13, 14, 19

## Required remediation

1. Consolidate to one physical CoreMotion owner behind `MotionService`; remove/retire the parallel controller path.
2. Expose the required attitude + rotation-rate records through that service, with a bounded buffer.
3. Record/bridge the accepted-still monotonic timestamp and bind motion automatically at acceptance.
4. Add service-level tests for unavailable/update failure, valid attitude/rotation updates, bounded buffering, and exact alignment boundaries.

PL-0081 remains unchecked.

Decision: **CHANGES_REQUIRED**
