# CLAUDE_PEER_REVIEW: iOS Manual Capture live pipeline (PR #7), V01

- Reviewer: Claude Code independent peer reviewer (read-only on source). This is not a builder or tester report, CHATGPT_AUDIT or CODEX_PEER_REVIEW.
- Scope: `git diff main...fix/ios-capture-button-visible`, commits ae1ef7cd and f68a265d (HEAD f68a265da265bdfd15b218fffb6734d7c02793a3)
- Verdict: **FAIL (CHANGES_REQUIRED)**. There is one blocking finding (H1), and the change is small. Everything else is PASS_WITH_NOTES quality.
- Compile/XCTest: **NOT_VERIFIED**. At review time, PackLab Capture macOS CI run 44742386417 on f68a265d was still in_progress. The only compiler is CI, so acceptance also needs that run to be green with 220 executed tests and 0 failures.

## Locally verified evidence
- `python -m pytest tests/packscan/test_ios_row_button_styles.py tests/packscan/test_swift_authoritative_contracts.py -q`: 6 passed.
- `func test` count in PackLabCaptureTests.swift: main 217, then head 220 (+3). The workflow `all) expected=220` (.github/workflows/packlab-capture-macos.yml:579) matches exactly. No other test files carry `func test`.
- ManualCaptureCoordinator, QualityDecisionPolicy and the M04 thresholds are unchanged. Quality problems still only produce warnings for a manual override, and the hard blocks (health, camera, session, source, metadata, pose) are intact. This PR does not weaken any safety rule.

## Findings

### HIGH (blocking)
**H1. Rapid repeated Manual Capture taps can reuse a sequence number and drop an acceptedID.** Locations: apps/ios-capture/PackLabCapture/ContentView.swift:505-516 (state read and `next` precomputed), :477 (commit), :923-927 (the button has no in-flight disable).
- requestManualCapture reads state.json and builds `next` (nextSequence+1, acceptedIDs+[id]) BEFORE it awaits the shutter and the store transaction.
- The StillCaptureGate in HighResolutionStillCaptureService only covers the camera request. It is released (CameraFoundation.swift:384, deferred gate.end) as soon as the still is returned, which is before storeAcceptedCapture and the photos.json append run.
- So a second tap that lands after the shutter of capture 1 but before its state commit reads the stale state N. It then captures successfully and commits record sequence N plus a state whose acceptedIDs lacks capture 1. Each call also builds a fresh ScanSessionStore, so the actor never serializes the two.
- The result is duplicate sequence values in accepted records and photos.json, and state.acceptedIDs silently loses an accepted photo whose record and source stay on disk.
- Fix, either of these:
  - (a) Add a published manualCaptureInFlight guard to requestManualCapture (return a capture_in_flight block) and disable the button while it is set.
  - (b) Derive sequence/acceptedIDs from the on-disk state inside the store transaction.
- Add a regression test: two concurrent requestManualCapture calls must yield distinct sequences and both IDs in acceptedIDs, or one of them must be blocked.

### MEDIUM (non-blocking, follow-up recommended)
**M1. photos.json is not inside the session transaction.** Location: ContentView.swift:477-480 and CameraFoundation.swift:754-773.
- The pre-validation (manualPhotoMetadata before the commit) is good. But if appendForCommittedSource fails after storeAcceptedCapture has committed (I/O error, a corrupt existing photos.json, or duplicatePhoto), the source, record and state stay committed while photos.json lacks the entry.
- The UI then reports capture_persist_failed even though the photo was accepted, and finalizeCanonicalAcceptedSession (SessionFoundation.swift:308-309, imagePath set equality) fails for this session permanently.
- Fix: a repair path that rebuilds missing photos.json entries from committed records/sources, or a txn marker that finalize/reopen can reconcile.

**M2. Gallery Delete/Retake do not update photos.json.** Location: SessionFoundation.swift:334-347 and :804/:814, wired in the UI.
- This PR is what makes photos.json authoritative for manual captures. After the operator deletes or retakes a manual photo, the imagePath set in photos.json no longer equals the records, so Finalize fails with the generic message.
- Before this PR finalize was already impossible, so this is not a regression, but the path is now reachable.

**M3. The 2 Hz candidate log evicts manual audits.** Location: ContentView.swift:410-412 and :462-464, M04CaptureEngine.swift:604-610 (maximumRecords 2048, full load/decode/rewrite per append).
- Each tick decodes and rewrites the whole quality log and also rewrites the M04 context (persistBasePassContext). This costs real I/O.
- After about 17 minutes of live view, candidate rows push out the blocked-manual-attempt audit rows, which are only stored in this log. Accepted captures keep their audit in the record.
- Fix: keep manual audits in a separate log, or stop logging unchanged candidate decisions.

**M4. Manual gating has no freshness check on m04Evaluation.** Location: ContentView.swift:442 and :517.
- The poseReady and quality inputs come from the last tick, which can be up to 0.5 s old. If the loop stops (stop(), AR paused for QR pairing because currentCandidateFrame returns nil when not started, or after resume), the value can be arbitrarily old.
- The persisted pose binding is taken honestly at shutter time from the shared AR buffer, so stored evidence is not fabricated. The gate decision, however, can rest on stale evidence.
- Fix: block when (monotonicTimestamp - evaluation.input.monotonicTimestamp) exceeds a small bound. Both values are in the uptime domain on device.

### LOW / notes
- **L1. Loop not restarted.** stop() cancels the loop (ContentView.swift:136), but start() (:110-130) never restarts it, so after a stop/start cycle the live loop stays off until New Scan or Resume. Today stop() appears to have no production caller, so this is latent.
- **L2. Loop not tied to session end.** The loop keeps writing the quality log and context into the active session directory after finalize or discard, and QualityCandidateLogStore.write recreates directories. It should stop on finalize or when the active session is discarded.
- **L3. Sequence counter resets.** The candidate sequence counter restarts at 0 on every startLiveCandidateLoop (:537), so quality-log sequences repeat across restarts and share a field with the record sequences of manual audits. Candidate IDs are UUIDs, so rows stay distinguishable.
- **L4. Exposure/WB read after the shutter.** acceptedMetadata reads exposure/ISO/WB from the AVCaptureDevice after the still returns, under ARKit-driven continuous auto exposure, and labels them available/device_api (:496). This is the same pre-existing behavior as :758 and is a real device reading, but it is not shutter-synchronous. Prefer the still EXIF when present. Focal length is correctly left unavailable, and a missing lens is recorded as an app-only "unavailable" identity (not in the wire).
- **L5. Orientation source label.** Orientation is derived from the stored pixel dimensions, but the wire labels the source exif (pre-existing wire choice). This is consistent with the HEIC being written with EXIF orientation 1 (ARTrackingService.swift:312), so it is acceptable.
- **L6. Legacy sessions.** Sessions captured with earlier builds (all sequence 0, no photos.json) remain unfinalizable, and resuming one and adding captures yields a partial photos.json. The new finalize message only covers invalidManifest (no records).
- **L7. Motion merge cost.** The motion fallback appends records one by one into MotionBuffer, which re-sorts on every append, and keeps only the newest 256. This is acceptable at current rates.
- **L8. Sampler cost.** The 64x48 sampler does about 49k byte reads per tick on the main actor at 2 Hz, which is negligible. It holds the ARFrame only for the duration of the call. Sharpness thresholds remain provisional, and there is no on-device calibration claim.

## Production-path and test assessment
- **Wiring.** bindProductionARCamera binds the frame and pose sources on device only (not in the simulator). The loop is started from New Scan and Resume, is a no-op without a source, and is cancelled in stop()/deinit. It uses weak self with sequential ticks and no overlap. Swift 6 isolation looks sound: the class is MainActor, the closures are MainActor, and only the Sendable QualityImageFrame and timestamp leave SharedARSessionOwner. A CoreVideo import inside a top-level #if mid-file is legal. Final confirmation still depends on the in-progress CI.
- **Pose binding.** Empty caller buffers fall back to the live AR poseBuffer, which contains the still frame pose via recordCapturePose, and the binding is keyed on still.monotonicTimestamp. This is honest capture-time binding. storeAcceptedCapture(still:) re-binds with the same buffers, which is consistent.
- **testManualCaptureEndToEndFromLiveFrameToFinalizedPackScan.** This test drives the real production entries (analyzeLiveCandidateFrame, analyzeM04Candidate, requestManualCapture, captureAndPersistManual, ScanSessionStore, AcceptedPhotoMetadataStore, ProductionScanFinalizeAction) through the bindLiveCandidateSources / bindStillCaptureBackend injection seams. The assertions are meaningful: state advance, acceptedIDs, photos.json imagePath, pose status, coverage sector and exported state. Gaps:
  - It covers only one capture. No repeated or concurrent capture is tested, which is how H1 went unnoticed.
  - startLiveCandidateLoop() is called before the sources are bound, so the loop itself never runs. The tick is called manually.
  - It is a synthetic wiring proof (JPEG bytes named .heic, injected pose). It is correctly labelled as such and makes no device-quality claim.
- **testManualCaptureWithoutLiveFrameIsBlockedWithExplanatoryReason.** This is a genuine negative path: zero backend requests and no record.
- **testLiveQualityFrameSamplerNormalizesLumaPlane.** The expected values are hand-derived (2c+0.5; 16 maps to 0 and 235 to 1). It is not tautological.

## Required before PASS
1. Fix H1 and add a repeated/concurrent manual capture regression test (update the count guard accordingly).
2. CI on the new head must be green: Simulator XCTest (exact count) plus the unsigned archive.
3. Real-iPhone acceptance remains a separate owner gate. This review does not claim device behavior.
