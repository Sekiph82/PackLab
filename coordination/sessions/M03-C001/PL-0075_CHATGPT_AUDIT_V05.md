# PL-0075 — ChatGPT Independent Audit V05

Decision: **CHANGES_REQUIRED**

## Independent finding

White balance is now wired through the production AVFoundationCameraControlComposition and accepted-photo metadata path. The remaining V05 requirement is still unproven: tests do not drive the physical selected-device adapter through adjustingWhiteBalance stabilization, lock-before-stable rejection, lock-after-stable success, wrong-device rejection and runtime/persisted metadata propagation. Existing tests cover pure policy/bridge behavior rather than the production AVFoundation adapter seam.

## Required remediation

Preserve the current production composition. Introduce the minimum production-used injectable camera-device control seam necessary to test the AVFoundation adapter behavior without a physical iPhone, then add behavior-bearing tests for the exact wrong-device/stabilization/lock/runtime/metadata cases required by the frozen V05 criteria. Do not replace the working camera architecture with a parallel helper.

PL-0075 remains unchecked.

Decision: **CHANGES_REQUIRED**
