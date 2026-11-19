# CLAUDE_PEER_REVIEW — iOS single camera owner (PR #3) — V01

- Reviewer: independent Claude Code reviewer subagent. I did not author this change, and this is not a CHATGPT_AUDIT or CODEX_PEER_REVIEW.
- Scope: software only. The iPhone 16 device run is separate evidence and was not inspected here.
- Base: `origin/main` (39a1331d). Head: `origin/fix/ios-single-camera-owner` @ `2eb6c68407773bd692709fd1a7d40882a10c4278` (1 commit).
- Diff: 8 files, +518/-306. Inspected with `git diff origin/main...origin/fix/ios-single-camera-owner` and `git show BRANCH:PATH`. No branch switch and no source edits.

## Verdict: FAIL (CHANGES_REQUIRED)

The design is sound and is the right fix for the camera contention. There are two blocking problems, neither of them in the design:

1. The Swift code has never been compiled. Hosted macOS CI never ran (run 44591965477: "The job was not acquired by Runner of type hosted even after multiple attempts"; both jobs were cancelled and the run concluded failure).
2. A required check is red: Locked Python quality (run 44591965703) fails at "Ruff format changed Python files".

With a green macOS run (build, 214 XCTests, device archive) and the ruff fix, I would expect this to become PASS_WITH_NOTES, provided the P2 items are fixed or explicitly accepted.

## CI evidence (checked myself with `gh pr checks 3` and `gh run view`)

| Check | Result |
|---|---|
| Scan tracked repository for signing material | pass |
| Locked Python quality | **fail**: only the "Ruff format changed Python files" step. Ruff lint, Mypy, and Unit and repository tests passed. |
| Unsigned iOS Simulator build and XCTest | **cancelled**: no runner acquired. NOT_VERIFIED. |
| Unsigned iOS device archive | **cancelled**: no runner acquired. NOT_VERIFIED. |

Local evidence (Windows):
- `pytest tests/packscan/test_swift_authoritative_contracts.py` on an extracted copy of the head tree: 4 passed.
- `ruff format --check` on the **main** copy of that file: "1 file would be reformatted". The formatting debt predates this PR. The gate fails only because the PR touches the file.

## Findings

### P1
- **P1-1: compile and XCTest status unverified.** `.github/workflows/packlab-capture-macos.yml` jobs were cancelled before they started. Under SWIFT_VERSION 6.0, SWIFT_STRICT_CONCURRENCY=complete and SWIFT_TREAT_WARNINGS_AS_ERRORS=YES (project.pbxproj:256-261), none of the new Swift has been built, and the 214 expected count is unproven. Re-run the macOS workflow (it needs an acquired runner) before merging. On a static read I found no definite compile error (see "Concurrency review").
- **P1-2: red required Python check.** `tests/packscan/test_swift_authoritative_contracts.py` must be `ruff format`-ed, because the workflow formats every changed Python file. The fix is mechanical and needs no logic change.

### P2
- **P2-1: there is no time limit after Retry or restart.** `CameraFoundation.swift:798`, `:927-928`, and `ContentView.swift:583` (`restartCamera()`). The timeout is scheduled only on `.interruption` (`CameraFoundation.swift:923`). If the operator taps Retry while the camera is still held elsewhere, `restartCamera()` re-runs the session and the machine enters `.restarting`. If ARKit does not deliver a frame (no `.restartSucceeded`) and does not re-emit `sessionWasInterrupted`, the machine stays in `.restarting` forever. The UI then shows "Camera interrupted. Reconnecting…" with no Retry button (the button appears only for `.blocked` and `.failed`, `ContentView.swift:725-726`). That is the original device symptom again, reached through Retry. The `.runtimeError` -> `.restarting` path has the same gap. Fix: arm the same token-guarded timeout when entering `.restarting`, moving to `.blocked` (or `.failed`) on expiry. Add one XCTest mutant for it.
- **P2-2: HEIC encode on the completion queue can stall the main thread.** `ARTrackingService.swift:237-241` and `:265-274`. Each still creates a new `CIContext()`, renders the full-resolution YCbCr buffer to a CGImage, and HEIC-encodes it inside the `captureHighResolutionFrame` completion. The code comment itself says this queue is main by default. That is plausibly 100-300 ms on the main thread per still. Session-delegate frames (pose buffer, `noteFrameDelivered`), the 100 ms refresh loop and SwiftUI would stall during guided capture. Correctness holds because the still records its own frame pose. The `ponytail:` note is honest, but this is a capture app, and a reused static `CIContext` plus `Task.detached` or a utility queue costs only a few lines. At minimum, cache the `CIContext`. Otherwise this must be measured in the device run before acceptance.

### P3
- **P3-1: one assertion passes for the wrong reason.** `PackLabCaptureTests.swift:1731` ("a stopped session must not capture"). XCTest runs on the Simulator, where `captureHighResolutionStill` always throws `.unavailable` (`ARTrackingService.swift` `#if targetEnvironment(simulator)` branch). The assertion therefore still passes if the `guard isStarted` is deleted. The continuation, token and cancel logic (`finishStill` and `cancelStillCapture`: stale completion after cancel, `capture_in_flight`) is device-only and has no test. Consider extracting the continuation bookkeeping behind a fakeable `captureHighResolutionFrame` seam.
- **P3-2: `cameraUnauthorized` -> `.permission(.denied)` mapping is untested.** `ARTrackingService.swift:207`. The tests use only a generic `NSError`. A mutant that always emits `.runtimeError` survives, and a denied user would then see three restart attempts and then "could not restart".
- **P3-3: operator Retry is logged as `runtimeError`.** `ContentView.swift:583` calls `owner?.restartCamera()` with the default `reason: .runtimeError`, so a Retry is recorded as `.runtimeError` in `resetDiagnostics` and the epoch reason. Pass `.userRequested` for the retry path, or give the restart closure a reason.
- **P3-4: no persisted evidence uses the exact-pose binding yet.** `recordCapturePose` writes into `SharedARSessionOwner.poseBuffer`. However, the production manual-capture path persists `poses: PoseBuffer()` (empty), as it already did before this PR (`ContentView.swift:471`). The `ARCapturedStillFrame.intrinsics` and transform are held only in `ARSessionStillCaptureBackend.lastCapture` and are never persisted. There is no `.packscan` schema or authority change, which is correct. But `docs/development/NEXTLEVEL_PIN.md` ("timestamp, camera-to-world pose and intrinsics come from that same ARFrame") should not be read as a claim that persisted evidence now carries an exact pose or intrinsics.
- **P3-5: orientation and intrinsics semantics changed but were not checked on a device.** Stills are now stored in sensor orientation with EXIF orientation 1, so a portrait-held phone produces landscape pixels. The former AVCapturePhoto path normally wrote rotated-orientation EXIF. That is honest as storage, but it is a behavior change for downstream viewers and PackScan or Scan Master consumers. Two things remain unconfirmed: that `ARFrame.camera.intrinsics` on the high-resolution frame matches `capturedImage` dimensions, and that `exifData` carries no conflicting orientation. Confirm both on the device run with one decoded HEIC.
- **P3-6: control-readout churn.** `ContentView.swift:145-146` calls `observeFocus()` and `observeWhiteBalance()` every 100 ms. That publishes a new controls state each time and re-renders the view. `AVFoundationWhiteBalanceAdapter.observe` always returns `.stabilizing`, so the WB label never settles. Any observe error overwrites the "ARKit-managed..." note with "Focus unavailable". The labels are honest (`device_api`, read from `configurableCaptureDeviceForPrimaryCamera`), but readings are taken at accept time, not at the frame timestamp. That timing skew already existed.
- **P3-7: the Python guard checks only two files.** `tests/packscan/test_swift_authoritative_contracts.py:104-110`. I judge the change legitimate overall (see "Python guard assessment").
- **P3-8: leftover NextLevel references.** NextLevel is still in `project.pbxproj` (6 refs) and `Package.resolved`, which the doc acknowledges, so the dependency is still linked although unused. Stale comments remain in `Services/CameraService.swift:30` ("NextLevel-backed camera adapter") and `Services/PairingProtocol.swift:53` ("AVCapture/NextLevel session"). No `import NextLevel` and no use of the removed types remains anywhere in the app or tests.
- **P3-9: accessibility.** The More menu (`ContentView.swift:827-838`) has a correct `accessibilityLabel` and text-titled items. The hint always mentions "AR preview", even when `ARPreviewFeatureFlag` hides that item. This is a nit. "Retry camera" is a text button and is accessible.
- **P3-10: QR pause and restore are correct in logic but unverified on a device.** Install is at `ContentView.swift:585-589`. `stop()` pauses the session and emits `.stopped`, which takes the machine to idle and cancels an in-flight still. `restore` calls `start()`, which sets a pending `.started` that the first frame confirms. Pairing is gated by `PairingCameraOwnership` (`PairingProtocol.swift:224-240`), so restore runs only if capture was displaced. Two points remain open:
  - `ARSession.pause()` may release the camera asynchronously, so the QR `AVCaptureSession` could see a brief interruption.
  - Resuming without `.resetTracking` keeps the epoch across the pairing gap, and this is not checked against relocalization.

  Both need the device run. Neither path has an XCTest.

## State machine review (my own reasoning)
- `CameraRecoveryMachine` handles these cases correctly:
  - `.interruptionTimedOut` acts only from `.interrupted`.
  - A late `.interruptionEnded` recovers from `.blocked`.
  - `.retry` acts only from `.blocked` or `.failed` and resets `retryCount`.
  - `cameraReady` now excludes `.blocked` (`ContentView.swift:470`).
- `CameraRecoveryOwner` uses a token plus a `state == .interrupted` guard. That defeats stale timers from an earlier interruption and timers that fire after recovery, and the test exercises both cases.
- No double session run: `sessionInterruptionEnded` runs the driver itself and sets `isEmittingInterruptionEnded`, so the synchronous `restartSession` -> `restartCamera()` re-entry is suppressed. The test checks that `driver.runs` equals `[false, false]`. Removing the guard yields `[false, false, true]`, which the test catches.
- Running only on the first frame (`pendingFrameSignal` consumed in `didUpdate`) is honest evidence that the camera is running.
- The old behavior of re-running the session inside `sessionWasInterrupted` is gone, which was correct. The epoch is still invalidated on interruption. The modified legacy assertion (`.recovering` -> `.interrupted` after `sessionWasInterrupted`) reflects that intended semantic change. It does not hide a regression.
- Background or a call lasting more than 6 s -> `.blocked`, then the late `interruptionEnded` -> `.restarting` -> first frame -> `.running`. This is correct.

## Concurrency review (static; compiler NOT_VERIFIED)
- The `captureHighResolutionFrame` completion is an explicitly `@Sendable`, nonisolated closure. This avoids the Swift 6 trap where a closure is inferred `@MainActor` and then trips `dispatch_assert_queue` when ARKit calls it off-main.
- `encodeStill` and `rowMajor` are `nonisolated static`. The hop back is a MainActor `Task` that captures self weakly, carrying a `Result<ARCapturedStillFrame, any Error>`, which is Sendable.
- `withCheckedThrowingContinuation` runs synchronously in the MainActor isolation of the caller, so setting `stillContinuation` there is fine.
- `ARSessionStillCaptureBackend` is a `@MainActor` class that satisfies the nonisolated async `StillPhotoBackend`. The removed `NextLevelStillCaptureAdapter` used the same pattern and compiled.
- The `TimeoutScheduler` action is `@MainActor @Sendable`, and the production scheduler uses a MainActor `Task`.
- Delegate methods rely on `@preconcurrency ARSessionDelegate` with the default (main) delegate queue. That pattern is unchanged.

## RealityKit delegate question
`SharedARCameraPreview` (`ARTrackingService.swift:318-321`) assigns `view.session = SharedARSessionOwner.shared.session` with `automaticallyConfigureSession: false`. That is the same pattern as the existing, accepted `ARPreview.swift:159-162`. The RealityKit ARView renders through internal session observation and does not take `ARSession.delegate` (Apple samples set `arView.session.delegate` themselves). I consider delegate theft low-risk. If it did happen on a device, the first-frame `.started` signal and pose samples would never arrive: the camera state would stay idle and pose readiness would block capture. The device run would expose it.

## Python guard assessment (`tests/packscan/test_swift_authoritative_contracts.py`)
The change is legitimate and does not weaken the guard. The three removed assertions pinned strings in NextLevel code that no longer exists. Their replacements assert the new single-owner composition:
- `SharedARCameraPreview()`
- `bindProductionARCamera()`
- `ARSessionStillCaptureBackend(source: owner`
- `captureHighResolutionFrame`
- `recommendedVideoFormatForHighResolutionFrameCapturing`
- the `.blocked` transition

They also add a new negative guard: no `import NextLevel` and no `AVCaptureSession()` in ContentView or CameraFoundation. All the earlier control-composition assertions are kept.

It could be stronger (P3-7):
- `let recovery = cameraRecoveryOwner` is a weak proxy. Asserting `recovery.handle(signal)` and `recovery.setSessionRestart` would actually pin the recovery wiring.
- The negative guard covers two files. Scanning all `PackLabCapture/**/*.swift` except `PairingProtocol.swift` would catch a second camera client added in a new file.

## Test mutant analysis (4 new XCTests; 210 -> 214 is consistent, and no test was removed)
- `testCameraRecoveryBoundsAnUnendedInterruptionAndKeepsLateRecovery` catches:
  - an unconditional timeout
  - a late end missing from `.blocked`
  - retry from `.running`
  - a missing `retryCount` reset
- `testCameraRecoveryOwnerTimesOutAnUnendedInterruptionAndRetriesOnRequest` catches:
  - a missing token check (stale first timer)
  - a missing state check (timer fired after recovery)
  - a double restart on a second retry
- `testARSessionStillBackendTakesBytesTimestampAndPoseFromTheSameFrame` catches:
  - a pose recorded before validation (count would be 2)
  - a stale `lastCapture`
  - a non-zero delta binding
- `testSharedAROwnerIsTheSingleCameraOwnerAndReportsFrameBackedCameraSignals` catches:
  - a re-run during an interruption
  - a double run on `interruptionEnded`
  - signals sent before the first frame
- Weak spots: P3-1 and P3-2.

## Not verified by this review
- Swift compilation, XCTest execution and the device archive (CI never ran).
- All on-device behavior: the high-resolution format on iPhone 16, encode latency, HEIC orientation and intrinsics, ARView delegate behavior, and the QR pause/resume camera hand-off.
