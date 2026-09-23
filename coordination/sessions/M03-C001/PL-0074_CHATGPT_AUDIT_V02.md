# PL-0074 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `034134005f3057b8de8356999791d7bd824ceff7`

## Independent result

The remediation improves the exposure domain model:
- finite exposure seconds / integer ISO / finite bias are validated;
- metering and lock are separate states;
- later M03 remediation adds PackScan-compatible photo metadata persistence;
- AVFoundation exposure configuration can route through a shared device coordinator when one is supplied.

The required end-to-end exposure integration remains incomplete.

### 1. Shared selected-camera configuration is still optional

`AVFoundationExposureAdapter.configure` / `.lock` accept an arbitrary `AVCaptureDevice` and an optional coordinator.

There is no mandatory selected-main-wide identity check before exposure mutation, so the physical exposure path is not guaranteed to target PL-0070's selected camera.

### 2. ExposureCaptureBinding is not connected to accepted-photo metadata

Final `main` contains both:
- `ExposureCaptureBinding`;
- `AcceptedPhotoMetadataStore` / `PhotoCaptureMetadata`.

But no inspected code maps an actual device exposure reading / binding state into the `PhotoCaptureMetadata.exposureSeconds` and `iso` fields at still acceptance.

The metadata store persists values supplied by callers; it does not prove those values came from the configured capture-ready camera state.

### 3. User-visible exposure state remains unintegrated

`CameraCaptureControlModel` can hold `.metering`, `.locked`, `.unavailable`, `.failed`, but no SwiftUI capture UI/view model consumes and displays those states.

### 4. Required integration tests are missing

The new XCTest validates only the pure `ExposureCaptureBinding` value rules.

It does not cover:
- selected-device mismatch;
- unsupported physical lock;
- serialized device mutation;
- capture-ready exposure-to-photo-metadata binding;
- visible failure/unavailable state.

## Criteria

- PASS: 1-9, 15-18
- FAIL: 10, 11, 12, 13, 14, 19

## Required remediation

1. Make the selected main-wide camera configuration owner mandatory and fail closed on device mismatch.
2. Capture actual device exposure/ISO at the accepted-still boundary and map it into PackScan photo metadata automatically.
3. Bind exposure state to the real capture UI/view model.
4. Add integration tests for selected-device enforcement, unsupported lock, metadata binding and UI state transitions.

PL-0074 remains unchecked.

Decision: **CHANGES_REQUIRED**
