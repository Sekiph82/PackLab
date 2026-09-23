# PL-0079 — ChatGPT Independent Audit V01

Decision: **CHANGES_REQUIRED**

Implementation commit: `91971e27f61cd79ae6b94fc4639a1cd763da8c26`

## Independent findings

The child correctly:
- uses `ARWorldTrackingConfiguration`;
- guards `ARWorldTrackingConfiguration.isSupported`;
- avoids LiDAR-only scene depth/mesh reconstruction;
- maps AR tracking states and interruptions into explicit policy states;
- adds deterministic lifecycle-policy tests;
- keeps the ARSession implementation out of SwiftUI.

However it does not satisfy the required architecture seam.

### Existing ARTrackingService is bypassed

M01 already defines the project’s `ARTrackingService` protocol and simulator fallback. This child introduces a separate `ARWorldTrackingController` with its own public `ARSession`, `start()`, `stop()`, and `policy`.

It does **not** implement or adapt the existing `ARTrackingService` protocol, and no composition layer makes `ARWorldTrackingController` the physical implementation behind that seam.

Therefore:
- criterion 11 / Requirement B fails;
- criterion 13 / Requirement D is incomplete because two AR ownership abstractions now coexist;
- simulator `.unavailable` remains in the old service, while physical state lives in a separate controller, so the shared service contract is not coherent.

## Criteria

- PASS: 1-10, 12, 14-18
- FAIL: 11, 13, 15, 19-20

## Required remediation

1. Make the physical ARKit implementation conform to or sit behind the existing `ARTrackingService` seam.
2. Establish one ARSession owner for the capture app and prevent duplicate controller/session creation.
3. Preserve the simulator `.unavailable` implementation under the same service contract.
4. Expose truthful running/limited/unavailable/interrupted state through the common service/model.
5. Add lifecycle/capability tests against the service seam and publish a complete child log checkpoint.

PL-0079 remains unchecked.

Decision: **CHANGES_REQUIRED**
