# PL-0073 — ChatGPT Independent Audit V05

Decision: **CHANGES_REQUIRED**

## Independent finding

The production camera-control composition is now bound from the selected main-wide device into CaptureRuntimeViewModel, but the V05 frozen criteria explicitly require behavior tests for wrong-device rejection, adjusting-focus→stable observation, lock-before-stable rejection, lock-after-stable success, and runtime propagation at the production-used physical adapter seam. The Swift test target still contains no CameraDeviceConfigurationCoordinator / AVFoundationFocusAdapter / nonSelectedDevice / stabilizationRequired coverage. Existing tests exercise CameraControlRuntimeBridge and policy models only.

## Required remediation

Preserve the current production composition. Introduce the minimum production-used injectable camera-device control seam necessary to test the AVFoundation adapter behavior without a physical iPhone, then add behavior-bearing tests for the exact wrong-device/stabilization/lock/runtime/metadata cases required by the frozen V05 criteria. Do not replace the working camera architecture with a parallel helper.

PL-0073 remains unchecked.

Decision: **CHANGES_REQUIRED**
