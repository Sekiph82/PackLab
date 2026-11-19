# NextLevel package pin

Checked: **2026-09-20**. PackLab pins the canonical [`NextLevel/NextLevel`](https://github.com/NextLevel/NextLevel) Swift package at exact version **0.19.1** in `PackLabCapture.xcodeproj/project.pbxproj`.

- Repository: `https://github.com/NextLevel/NextLevel`
- Exact tag: `0.19.1`
- Immutable tag object verified with `git ls-remote`: `3daaa0604f98936a9b79381bc76e89d283ac5028`; peeled source commit: `edb3ba52aed8b49e9e197a275ea5e4846fb8c36d`
- Upstream license: MIT, per the repository [LICENSE](https://github.com/NextLevel/NextLevel/blob/main/LICENSE)
- Pinned-manifest compatibility evidence: the [`0.19.1` `Package.swift`](https://github.com/NextLevel/NextLevel/blob/0.19.1/Package.swift) declares iOS 16 as the package deployment floor. This pinned manifest is the authoritative source for that compatibility fact; it is not inferred from README migration prose.

NextLevel is a camera-control implementation detail behind PackLab-owned camera-service interfaces. Cross-platform contracts and domain code must not expose NextLevel types or depend on its internal API. The package is present in the Xcode package graph but is not imported by the foundation UI in this child.

## Camera ownership (2026-11 device run)

The capture screen no longer imports NextLevel. On the first iPhone 16 run, the NextLevel `AVCaptureSession` and the shared ARKit `ARSession` both requested the rear camera. iOS grants it to one client at a time. The capture session therefore stayed interrupted with "Reconnecting…".

The shared `ARSession` (`SharedARSessionOwner`) is now the only camera client on the capture screen:

- Preview: `SharedARCameraPreview`, rendered from that session.
- Tracking: the same session.
- Stills: `ARSession.captureHighResolutionFrame`, using `recommendedVideoFormatForHighResolutionFrameCapturing`.

Each still is the frame's `capturedImage`, encoded as HEIC by the app on a background queue. The image keeps stored sensor orientation (EXIF orientation 1) and carries ARKit's `exifData`.

The still's monotonic timestamp comes from that same `ARFrame`. The app also reads the frame's camera-to-world pose and intrinsics, but holds them only in memory:

- The pose is added to the in-memory pose buffer.
- The intrinsics stay on the still backend.

Neither is persisted yet. No `.packscan` field, schema or authority changed, and persisted capture records do not yet carry a frame-exact pose or intrinsics. The manual capture path still binds pose as it did before.

Focus, exposure and white-balance readings still use `source: device_api`. They now come from `ARWorldTrackingConfiguration.configurableCaptureDeviceForPrimaryCamera`, which is the device ARKit drives. Those controls stay in continuous auto mode during AR tracking, and the app labels them as ARKit-managed.

The QR pairing scanner pauses the AR session before it opens its own `AVCaptureSession`. The NextLevel pin stays in the package graph, unused by the capture screen, until a separate task removes it.

## Validation boundary

Windows validation checked the repository URL, exact tag/revision, project graph strings, and absence of unrelated Swift dependencies. Native Swift Package Manager/Xcode package resolution and compilation require macOS/Xcode; they are not claimed from this checkout. The project’s Swift setting is aligned to `6.0` because upstream NextLevel 0.19.1 documents Swift 6, while full strict-concurrency settings are handled by PL-0039.
