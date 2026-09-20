# iOS Capture baseline

PL-0036 establishes a minimal native SwiftUI PackLab Capture project under `apps/ios-capture`. The product name and bundle identifier (`PackLabCapture` / `com.packlab.capture`) are intentionally distinct from Windows Studio.

## Device and deployment decision

The target is the owner-declared iPhone 16 Standard baseline. The project does not require LiDAR, Pro-only hardware, or a special camera mode. The minimum deployment target is iOS 17.0: it provides the SwiftUI/navigation baseline needed by this foundation while remaining below the iPhone 16 generation's shipped iOS baseline. Final device/runtime support remains subject to the applicable Apple SDK and owner-device verification.

Project settings are source-controlled and contain no personal Apple team identifier, signing identity, provisioning profile, credential, or private path. Later camera, ARKit, CoreMotion, permissions, diagnostics, simulator fallback, and NextLevel work remains behind PackLab-owned service boundaries.

## Evidence boundary

On this Windows checkout, static source/project inspection and text checks are available. Native `xcodebuild`, simulator, physical iPhone, signing, and camera validation require the authorized macOS GitHub Actions boundary and are not claimed here.
