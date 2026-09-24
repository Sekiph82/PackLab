# PL-0074 — ChatGPT Independent Audit V05

Decision: **CHANGES_REQUIRED**

## Independent finding

Exposure is now wired through the production AVFoundationCameraControlComposition and captureAndPersistAcceptedPhoto can persist observed exposure/ISO metadata. However the V05 criteria require behavior tests for wrong-device rejection, selected-device serialized configuration, bias/lock behavior, runtime propagation and persisted metadata at the physical adapter seam. The test target still does not construct or drive CameraDeviceConfigurationCoordinator / AVFoundationExposureAdapter; the current evidence is bridge/model/static-source coverage only.

## Required remediation

Preserve the current production composition. Introduce the minimum production-used injectable camera-device control seam necessary to test the AVFoundation adapter behavior without a physical iPhone, then add behavior-bearing tests for the exact wrong-device/stabilization/lock/runtime/metadata cases required by the frozen V05 criteria. Do not replace the working camera architecture with a parallel helper.

PL-0074 remains unchecked.

Decision: **CHANGES_REQUIRED**
