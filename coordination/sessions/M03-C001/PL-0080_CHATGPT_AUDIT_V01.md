# PL-0080 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `60ec7b8c5fb6f06bc933420cae7601a67a9c5085`

## Independent findings

The child adds a useful pure alignment helper:
- timestamped pose sample model;
- nearest-sample selection;
- explicit tolerance;
- stale/missing/unavailable outcomes;
- alignment delta;
- deterministic boundary tests.

But the frozen task is to **record AR camera transforms/tracking state and align them to accepted capture timestamps**.

### No ARFrame sampling implementation

The implementation does not consume `ARSessionDelegate.session(_:didUpdate:)` / `ARFrame`, does not extract `frame.camera.transform`, and does not record `ARFrame.timestamp`.

Therefore criterion 10 / Requirement A is not implemented.

### No accepted-capture binding

`PoseAligner.nearest` is a standalone function. No code connects an accepted still/capture timestamp to a pose buffer and persists an aligned pose record. Criterion 11 fails.

### Timebase and transform semantics are not documented/validated

The new model uses a generic `TimeInterval` and `[Double]` transform without documenting the actual ARKit timebase, matrix order, or validating a 4×4/16-element finite transform. Coordinate conversion may be deferred to PL-0082, but the source semantics still need to be explicit. Criteria 12-13 are incomplete.

The synthetic test covers available/stale/missing/unavailable cases but not out-of-order multiple-sample behavior as explicitly required.

## Criteria

- PASS: 1-9, 16-18
- FAIL: 10, 11, 12, 13, 14, 15, 19-20

## Required remediation

1. Sample real ARFrame timestamp, camera transform and tracking state from the one AR session owner.
2. Document the source timebase and raw ARKit transform semantics.
3. Maintain a bounded pose sample buffer and bind the nearest eligible sample to each accepted camera capture timestamp.
4. Validate transform shape/finiteness and fail closed for stale/missing/ineligible tracking.
5. Add deterministic tests for out-of-order samples, exact tolerance boundaries, invalid transforms, and accepted-capture binding.
6. Publish a complete task-specific log checkpoint.

PL-0080 remains unchecked.

Decision: **CHANGES_REQUIRED**
