# PL-0073 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `64ef55ff4b471b09a2bf3be2c1bbf126c98382e9`

## Independent result

The remediation improves the design:
- focus configuration and lock are now separate operations;
- `CameraDeviceConfigurationCoordinator` carries a selected lens and AVCaptureDevice;
- device configuration can be serialized through a shared lock owner;
- a capture-control state model can retain focus/exposure/white-balance state.

The previous audit is not fully closed.

### 1. Selected-main-camera binding is optional and not enforced

`AVFoundationFocusAdapter.configure` and `.lock` still accept an arbitrary `AVCaptureDevice` and an optional coordinator.

`CameraDeviceConfigurationCoordinator.isSelectedDevice` exists but is never checked before focus configuration. A mismatched front/ultra-wide/other device can therefore still be configured successfully.

This does not satisfy the requirement that focus control be bound to the deterministically selected main rear camera.

### 2. No observed autofocus stabilization phase

`configure` sets `.continuousAutoFocus` and immediately returns `.continuous`.

There is no observation of `isAdjustingFocus`, focus state/KVO, stable-frame count, elapsed stability window, or equivalent physical-device signal before lock is allowed. The separate `lock` function can be called immediately after `configure`.

The API is two-call, but the required guided autofocus/stabilization behavior is not implemented.

### 3. User-visible focus state is still not wired to UI

`CameraCaptureControlModel` is a pure model seam. No inspected SwiftUI/view-model integration displays focusing/continuous/locked/unavailable/failed states to the user.

### 4. Tests do not cover the repaired physical behavior

The new test only verifies that the pure control model retains independent state fields. It does not cover:
- selected-device mismatch rejection;
- unsupported focus capability;
- stabilization-before-lock timing;
- configuration failure;
- visible UI/view-model state transitions.

## Criteria

- PASS: 1-9, 15-18
- FAIL: 10, 11, 12, 13, 14, 19

## Required remediation

1. Make the selected main rear camera coordinator mandatory for physical focus configuration and fail closed when the device identity does not match.
2. Observe real autofocus stabilization before exposing/allowing lock.
3. Bind focus state into the actual capture view model/UI.
4. Add behavior-bearing tests for selected-device mismatch, unsupported focus, stabilization gating, lock timing and failure state.

PL-0073 remains unchecked.

Decision: **CHANGES_REQUIRED**
