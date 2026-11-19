# CLAUDE_PEER_REVIEW — iOS single camera owner (PR #3) — V02

- Reviewer: independent Claude Code reviewer subagent. I did not author this change, and this is not a CHATGPT_AUDIT or CODEX_PEER_REVIEW.
- Scope: software only. The iPhone 16 device run is separate evidence.
- Head reviewed: `origin/fix/ios-single-camera-owner` @ `da6ebc1edf3231e4a7f75f9c61ab36b5c5ca7203`.
- V01 head: `2eb6c684`. Commits since then:
  - `46ce32e5` (ruff format)
  - `da6ebc1e` (review fixes)
- Method: I read `git diff 2eb6c684 origin/fix/ios-single-camera-owner` and the branch files. I made no source edits and no git writes.

## Verdict: PASS_WITH_NOTES

All V01 P1 and P2 findings are resolved in source and confirmed by CI that I checked myself. The remaining notes are P3 and do not block merge. Device-run evidence is still required separately for the on-device behavior listed under "Not verified".

## CI evidence (verified with `gh run view`, all on head da6ebc1e)

| Run / job | Result |
|---|---|
| macOS 44596694871, Unsigned iOS Simulator build and XCTest | success. The log shows "Executed 217 tests, with 0 failures", `"totalTestCount": 217` and "TEST SUCCEEDED". |
| macOS 44596694871, Unsigned iOS device archive (attempt 2) | success. The log shows "ARCHIVE SUCCEEDED" (Xcode 16, Release, `generic/platform=iOS`). |
| Windows Python Quality 44596695626 | success, including the ruff format step |
| Signing Material Guard 44596694663 | success |

The device archive failed on attempt 1 with "xcodebuild: error: Unable to find a destination ... iOS 18.0 is not installed". That is a runner-image problem, not a code problem, and attempt 2 passed.

The archive result matters for this review. Code under `#if !targetEnvironment(simulator)` is compiled only by the device archive, never by the Simulator job. That code includes `ARStillEncoder`, `DeviceARSessionDriver` video-format selection, `SharedARCameraPreview` and `configureARCameraControls`. It is now compiled under Swift 6 with complete strict concurrency and warnings treated as errors.

## Disposition of V01 findings

| V01 | Status | Evidence (head da6ebc1e) |
|---|---|---|
| P1-1 compile/XCTest | RESOLVED | See the CI table: 217/217 tests pass and the device archive succeeds. |
| P1-2 ruff format | RESOLVED | `46ce32e5`; Python Quality run is green. |
| P2-1 no limit on restart wait | RESOLVED | See P2-1 below. |
| P2-2 encode on main thread | RESOLVED | See P2-2 below. |
| P3-1 stopped-session assertion passed for the wrong reason | RESOLVED | See P3-1 below. |
| P3-2 permission mapping untested | RESOLVED | See P3-2 below. |
| P3-3 Retry logged as runtimeError | RESOLVED | See P3-3 below. |
| P3-4 doc overstated persisted pose and intrinsics | RESOLVED | `NEXTLEVEL_PIN.md` now says the pose and intrinsics are held in memory only. It also says no `.packscan` field, schema or authority changed and that the manual path binds pose as before. This matches the source. |
| P3-5 orientation and intrinsics | OPEN (device evidence) | This needs a decoded HEIC from the device run. It is not a code defect. |
| P3-6 control-readout churn | RESOLVED | See P3-6 below. |
| P3-7 guard checks only two files | RESOLVED | See P3-7 below. |
| P3-8 stale NextLevel comments | RESOLVED | `CameraService.swift:30` and `PairingProtocol.swift:52-53` are reworded. The NextLevel package is still in the project graph, as the doc states. |
| P3-9 accessibility hint | RESOLVED | `ContentView.swift:855`: the hint follows `ARPreviewFeatureFlag`. |
| P3-10 QR pause/restore | OPEN (device evidence) | The logic is unchanged and still correct. The camera release timing and the epoch across the pause still need the device run. |

### P2-1: every restart wait is now bounded
- `CameraFoundation.swift:797`: `.interruptionTimedOut` now acts from `.interrupted` or `.restarting`.
- `:949` `restart(trigger:)`: arms the timeout before calling `restartSession`. All three restart paths go through it: `.interruptionEnded`, `.retry` and `.runtimeError`.
- `.restartFailed`: re-arms the timeout when the machine stays in `.restarting`.
- `:955`: the timer callback checks the token and the state (`.interrupted` or `.restarting`).

Every new arm increments the token, so a stale interruption timer cannot fire after a restart. A timeout during a slow but genuine restart self-heals: the pending `.restartSucceeded` frame signal still moves `.blocked` to `.running`. A late interruption-ended still goes through `restart(trigger:)`. There `restartCamera()` is suppressed by `isEmittingInterruptionEnded`, so the session still runs only once.

Test: `testCameraRecoveryOwnerBoundsEveryRestartWaitSoRetryCannotHang` (`PackLabCaptureTests.swift:1828`) covers runtimeError, then timeout to blocked, then Retry, then timeout to blocked again, then Retry, success and a stale timer, then restartFailed and its timeout. It would catch these mutants:
- dropping the arm in `restart`
- dropping `.restarting` from the machine transition
- dropping the restartFailed re-arm

### P2-2: still encode moved off the main thread
- `ARTrackingService.swift:291` `ARStillEncoder`: one shared instance, one reused `CIContext`, a private serial queue at `.userInitiated`.
- The ARKit completion only boxes the frame and dispatches it. The Sendable `Result` then hops back to the main actor through a `@MainActor` Task (`:247-253`).
- `@unchecked Sendable` is justified in the code comment and holds: the members are immutable and the queue is serial. `FrameBox` carries the immutable ARFrame snapshot to that queue.
- The archive compiled all of this with warnings treated as errors.

### P3-1: still-capture continuation is now injectable and tested
- `ARSessionLifecycleDriver.captureHighResolutionFrame` (`ARTrackingService.swift:78`) is a protocol requirement, so it is dynamically dispatched and injected drivers really override it. The default implementation (`:82`) calls the session on device and fails as unavailable on the Simulator. The owner no longer short-circuits on the Simulator.
- `testSharedAROwnerStillCaptureUsesOneTokenGuardedContinuation` (`:1734`) covers:
  - stopped session to `.unavailable` with no driver call
  - a second request while one is in flight to `capture_in_flight`
  - an ARKit error passed through
  - interruption cancelling the capture to `camera_interrupted`
  - a stale completion (code 8) after cancel being ignored, with the next capture resolving with its own completion (code 9)
- It would catch these mutants:
  - removing `guard isStarted`
  - removing the in-flight guard
  - removing the token check

### P3-2: permission mapping now tested
`testSharedAROwnerMapsCameraUnauthorizedToPermissionDenied` (`:1767`) checks two cases:
- `ARError(.cameraUnauthorized)` leads to `.denied` with no restart.
- A generic error leads to `.restarting` with one restart.

A mutant that always reports a runtime error is now caught.

### P3-3: Retry logged with its real reason
- `CameraRecoveryOwner.restartTrigger` is set in `restart(trigger:)`.
- `ContentView.swift:584` maps `.retry` to `.userRequested` and everything else to `.runtimeError`.
- The trigger sequence is asserted (`[.runtimeError, .retry, .retry]`).
- The ContentView closure mapping itself is not unit-tested; see N3.

### P3-6: focus throttled, white balance no longer polled
`ContentView.swift:626`:
- Focus is polled every 10th refresh (about once a second) and published only when it changes.
- A failed read keeps the last state and the ARKit-managed note.
- White balance is no longer polled, because its adapter has no settled state; the comment says so.

### P3-7: guard now scans the whole app
`tests/packscan/test_swift_authoritative_contracts.py`:
- It asserts `recovery.handle(signal)` and `recovery.setSessionRestart`.
- It scans every `PackLabCapture/**/*.swift` for `import NextLevel` and `AVCaptureSession(`, exempting only `PairingProtocol.swift` (`:144`).
- It pins the new `.interrupted || .restarting` timeout transition.

The change is legitimate and stronger than V01.

## New notes from this pass (all P3, non-blocking)
- **N1, message wording.** `CameraFoundation.swift:811`. A restart that times out after a runtime error now lands in `.blocked`, and `.blocked` always shows "The camera is still in use elsewhere (a call, FaceTime or another camera app)". After a runtime error that cause may be wrong. Consider a neutral message, or a separate reason, when the wait began from `.runtimeError`.
- **N2, guard exemption is wider than needed.** `test_swift_authoritative_contracts.py:144`. The `PairingProtocol.swift` exemption skips both checks, so an `import NextLevel` there would also pass. Exempting only the `AVCaptureSession(` check would be tighter.
- **N3, retry reason wiring not unit-tested in ContentView.** `ContentView.swift:584`. The `restartTrigger` to `ResetReason` mapping lives in a ContentView closure, and only `restartTrigger` itself is tested. This is low risk and diagnostics-only.
- **N4, the V01 review file is now in the PR.** The diff since V01 includes `coordination/sessions/M18-C001/CLAUDE_PEER_REVIEW_IOS_SINGLE_CAMERA_OWNER_V01.md`. The coordinator committed it. Its content is my V01 review. Its "FAIL" verdict applies to head `2eb6c684` only and is superseded by this V02.

## Unchanged accepted behavior
- No `.packscan` schema, field, metric unit or PackScan, Scan Master or Design Model authority change. No `schemas/` file is touched.
- Metadata sources stay honest: `device_api` comes from `configurableCaptureDeviceForPrimaryCamera`, and stills are stored in sensor orientation with EXIF orientation 1 and ARKit `exifData`.
- No test was removed. The count went 210 to 214 to 217. The workflow `all` expectation matches, and the focused groups use explicit names, so they are unaffected.

## Not verified by this review (device run)
- The high-resolution video format on iPhone 16 and its preview and tracking cost.
- Whether `ARFrame.camera.intrinsics` on the high-resolution frame matches the stored HEIC dimensions, and how the HEIC orientation renders in downstream consumers (V01 P3-5).
- That the RealityKit ARView leaves the shared session delegate alone. The first-frame `.started` signal is the observable check.
- QR pairing: camera release timing after `pause()`, and the epoch after resume (V01 P3-10).
- The original symptom: no more permanent "Camera interrupted. Reconnecting…" on device.
