# PL-0080 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `f5eb2f52f318974c75c3bf6f04fa26c8c1efc8aa`

## Independent result

The remediation materially improves AR pose capture:
- the single shared ARSession owner now consumes real `ARFrame` updates;
- raw camera-to-world transforms and ARFrame timestamps are buffered;
- buffer size is bounded and sorted;
- transform shape/finiteness and normal-tracking eligibility are checked;
- stale/missing/invalid-transform outcomes are explicit;
- source ARKit timebase semantics are documented.

The accepted-capture alignment requirement is still not closed.

### 1. Camera capture and AR pose timestamps are in different domains

`PoseSample.timestamp` uses ARKit's monotonic `ARFrame.timestamp`.

But `HighResolutionStillCaptureService.capture` records the accepted still time only as:

`AcceptedStill.capturedAt: Date`

which is wall-clock/UTC-like application time.

No monotonic capture timestamp or wall-clock↔monotonic synchronization bridge is recorded at the still boundary.

Therefore a caller cannot truthfully pass `AcceptedStill.capturedAt` into `ARKitTrackingService.bindPose(... timestamp: TimeInterval)` without inventing a conversion.

### 2. bindPose is not connected to the accepted-still flow

Final repository inspection found the `bindPose` method definition, but no accepted-capture orchestration path calling it after a still is accepted.

The implementation provides an alignment API but does not actually associate the AR pose with each accepted capture.

### 3. Exact tolerance-boundary coverage is incomplete

The new test binds an exact timestamp (10.1 to 10.1) with tolerance 0.1. It does not test a sample exactly at the maximum-age boundary (absolute delta exactly 0.1), immediately inside, and immediately outside.

The frozen remediation criterion explicitly asks for exact tolerance boundaries.

## Criteria

- PASS: 1-11, 15-18
- FAIL: 12, 13, 14, 19

## Required remediation

1. Record a monotonic timestamp at the actual still-capture event in the same timebase as ARFrame, or implement a documented/tested clock-domain bridge.
2. Bind the nearest eligible pose automatically as part of accepted-still orchestration and persist the binding.
3. Add tests for exact tolerance, just-inside, just-outside, stale/missing/ineligible tracking, and end-to-end accepted-still binding.

PL-0080 remains unchecked.

Decision: **CHANGES_REQUIRED**
