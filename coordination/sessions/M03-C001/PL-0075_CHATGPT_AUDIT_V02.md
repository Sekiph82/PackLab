# PL-0075 — ChatGPT Independent Remediation Audit V02

Decision: **CHANGES_REQUIRED**

Implementation commit: `27b59c203629a5417d52723ce8e33bdac1ec320c`

## Independent result

The remediation improves white-balance evidence handling:
- physical temperature can be read from `deviceWhiteBalanceGains`;
- only finite values in the accepted Kelvin range are wrapped as observed readings;
- configure and lock are separate calls;
- the capture binding rejects invalid/unavailable readings.

The required stabilization/integration behavior remains incomplete.

### 1. No real stabilization observation gates lock

`AVFoundationWhiteBalanceAdapter.configure` switches to `.continuousAutoWhiteBalance` and returns `.stabilizing`.

`lock` can then be called immediately. There is no observation of `isAdjustingWhiteBalance`, stable gain/temperature samples, elapsed stability window, or equivalent real-device condition before lock becomes eligible.

Thus the flow is split into two methods, but it is not physically driven by observed stabilization.

### 2. Selected-camera/session ownership is still optional

The white-balance adapter accepts an arbitrary AVCaptureDevice and an optional coordinator. No selected-main-wide identity check is mandatory before changing white-balance mode.

### 3. Actual observed reading is not bound to accepted photo metadata

Final `main` contains the observed temperature helper and PackScan photo metadata persistence, but no inspected path automatically maps the real `WhiteBalanceCaptureReading` into the accepted still's `white_balance_kelvin` field.

### 4. User-visible state and required tests remain incomplete

`CameraCaptureControlModel` is a pure state holder; no SwiftUI capture UI displays stabilizing/locked/unavailable/failed state.

The new test covers valid/infinite Kelvin and a manual state transition only. It does not test:
- real stabilization gating;
- selected-device enforcement;
- unsupported lock;
- configuration failure/recovery;
- capture-metadata binding;
- UI/view-model transition.

## Criteria

- PASS: 1-9, 11, 15-18
- FAIL: 10, 12, 13, 14, 19

## Required remediation

1. Observe real white-balance stabilization and permit lock only after an explicit stable condition.
2. Make selected main-wide camera/session ownership mandatory for physical WB mutation.
3. Bind actual observed WB reading/state into accepted photo metadata.
4. Surface WB state in the actual capture UI/view model and test success/failure/stability boundaries.

PL-0075 remains unchecked.

Decision: **CHANGES_REQUIRED**
