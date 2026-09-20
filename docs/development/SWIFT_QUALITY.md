# Swift quality policy

PackLab Capture uses Swift 6 language mode with complete strict-concurrency checking. The target enables `SWIFT_STRICT_CONCURRENCY = complete`, treats Swift warnings as errors, and enables targeted Clang/GCC correctness warnings. The project does not use a blanket warning-suppression flag or a global Sendable/concurrency escape hatch.

## Isolation expectations

- SwiftUI views and observable UI state are main-actor owned. UI entry points should use `@MainActor` when isolation is not inferred by the framework.
- Camera, AR tracking, motion, storage, and transfer services own mutable state behind an actor or another explicit synchronization boundary.
- Service protocols are `Sendable` where they cross task boundaries; values passed between services should be immutable and `Sendable`.
- Device-framework imports and callbacks belong inside the service that owns that device capability. Adapters must translate framework callbacks into service-owned values rather than exposing framework state globally.
- Do not use `@unchecked Sendable`, `nonisolated(unsafe)`, global mutable singletons, or warning suppression to bypass a concurrency diagnostic. Fix the ownership boundary or document a narrowly justified exception for independent review.

## Verification boundary

The source-controlled settings are the intended Swift 6/Xcode configuration. This Windows workspace can inspect the project file and run static checks, but it cannot run native `xcodebuild`, the iOS simulator, or device validation. A macOS/Xcode run must verify the effective Debug and Release settings, strict-concurrency diagnostics, and warning-as-error behavior before claiming native compilation evidence.
