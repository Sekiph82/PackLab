# PL-0079 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `1456fd6ec8ec1b20804a849234478a5202c9a2eb`

## Independent result

The architectural remediation is materially successful:
- physical ARKit now sits behind `ARTrackingService`;
- `SharedARSessionOwner.shared` is the single ARSession owner;
- the old controller forwards to that owner rather than allocating a second session;
- simulator fallback remains under the common service contract;
- normal/limited/interrupted/unavailable states are exposed.

One mandatory remediation criterion remains open.

### Missing lifecycle/capability tests against the service seam

Remediation criterion 13 explicitly requires lifecycle/capability tests against the shared service seam.

The implementation commit does not modify the XCTest target. Final `PackLabCaptureTests.swift` contains the existing simulator fallback check but no test exercising:
- physical/service state mapping via an injectable owner/driver;
- start/stop idempotency;
- limited/interrupted state mapping;
- unsupported ARWorldTracking capability;
- proof that multiple service/controller facades share one session owner.

Because the physical owner directly constructs `ARSession` and has a private initializer, the critical ownership/state behavior is not independently testable on the Windows builder or through a framework-independent seam.

## Criteria

- PASS: 1-12, 15-18
- FAIL: 13, 14, 19

## Required remediation

1. Introduce a testable AR session-owner/driver seam without creating a second physical ARSession architecture.
2. Add behavior-bearing service tests for start/stop, unsupported capability, normal/limited/interrupted/unavailable state mapping and shared-owner identity/idempotency.
3. Preserve the one physical `SharedARSessionOwner` and simulator no-evidence behavior.

PL-0079 remains unchecked.

Decision: **CHANGES_REQUIRED**
