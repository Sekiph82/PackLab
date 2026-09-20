# iOS simulator fallbacks

`SimulatorCameraService`, `SimulatorARTrackingService`, and `SimulatorMotionService` satisfy the existing service protocols so the foundation can initialize without physical capture hardware. They report unavailable states and do not generate synthetic camera frames, AR poses, motion samples, or successful capture results.

`PackLabRuntimeEnvironment` uses the compile-time `targetEnvironment(simulator)` check and has a safe physical-device branch. `SimulatorFallbackCapabilities` records that all hardware capabilities are unavailable and that sensor evidence is not synthetic. These fallbacks are injection seams, not a replacement for the physical-device architecture.

The owner’s iPhone 16 Standard baseline still requires macOS/Xcode and device evidence for camera authorization, real capture, AR tracking, motion behavior, non-LiDAR operation, storage/transfer integration, and performance. Windows static inspection does not claim any of that evidence.
