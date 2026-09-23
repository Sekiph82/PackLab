# PL-0084 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `d814ff5cb02f8e791a53367026cbd5e7bc4b9800`

## Independent result

The remediation materially improves reset execution:
- the single shared ARSession owner now calls `session.run(..., options: [.resetTracking, .removeExistingAnchors])`;
- reset reason increments a localization epoch;
- interruption-ended routes through the same reset owner;
- accepted-capture preservation and epoch isolation are modeled/tested.

The real orchestration remains incomplete.

### 1. Actual AR owner never marks the new epoch recovered or failed

`SharedARSessionOwner.reset` calls `epochCoordinator.reset(reason:)`.

But when AR camera tracking later becomes `.normal`, `cameraDidChangeTrackingState` only calls `policy.normal()`. It never calls `epochCoordinator.recovered()`.

Likewise no actual AR failure path calls `epochCoordinator.failed()`.

As a result, the physical owner's epoch coordinator can remain permanently `.relocalizing` after reset.

### 2. Tracking-degradation reset is not connected to the physical reset owner

The physical owner has user-requested and interruption-ended reset paths.

No inspected integration connects degraded-tracking policy/hysteresis to:

`owner.reset(reason: .trackingDegraded)`.

The pure `ResetOrchestrationModel` can model this reason, but it is separate from the actual ARSession owner.

### 3. Reset diagnostics are not persisted from the real owner

`ResetDiagnosticEvent` and its diagnostics array live only in `ResetOrchestrationModel`.

The actual `SharedARSessionOwner` owns only `SessionEpochCoordinator`; it does not append/persist reset diagnostic events or feed the project diagnostics/session evidence path.

### 4. Tests exercise the pure model, not real reset orchestration

The added test does not exercise:
- owner reset options;
- normal tracking causing epoch recovery;
- failed relocalization;
- interruption-triggered reset;
- degradation-triggered reset.

## Criteria

- PASS: 1-10, 12, 15-18
- FAIL: 11, 13, 14, 19

## Required remediation

1. Drive epoch recovered/failed state from real AR tracking/relocalization outcomes.
2. Wire tracking-degradation reset into the single AR owner when policy requires it.
3. Retain reset reason/epoch diagnostics from the real owner in the session/diagnostics evidence path.
4. Add testable owner-driver coverage for user, interruption and degraded resets plus recovery/failure.

PL-0084 remains unchecked.

Decision: **CHANGES_REQUIRED**
