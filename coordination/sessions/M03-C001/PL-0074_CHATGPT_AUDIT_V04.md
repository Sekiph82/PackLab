# PL-0074 — ChatGPT Independent Audit V04

Decision: **CHANGES_REQUIRED**

## Independent finding

Exposure composition and AcceptedPhotoMetadataFactory exist, but the production runtime never composes AVFoundationCameraControlComposition into CaptureRuntimeViewModel. The accepted-still persistence path is not shown receiving composition.acceptedMetadata, and wrong-device/physical adapter→UI→persisted metadata behavior is not tested end-to-end.

## Required remediation

Preserve all Batch-004 behavior that already passes. Close only the remaining production-seam or evidence gap above with behavior-bearing tests against the actual production-used seam. Do not add another disconnected helper.

PL-0074 remains unchecked.

Decision: **CHANGES_REQUIRED**
