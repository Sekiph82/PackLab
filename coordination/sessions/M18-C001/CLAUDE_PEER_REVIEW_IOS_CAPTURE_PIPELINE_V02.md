# CLAUDE_PEER_REVIEW: iOS Manual Capture live pipeline (PR #7), V02 re-review

- Reviewer: Claude Code independent peer reviewer (read-only on source). These are my own findings. This is not a builder or tester report, CHATGPT_AUDIT or CODEX_PEER_REVIEW.
- Scope: `git diff f68a265d..c875c523` (e6ba1860, 29a4bf15, c875c523), checked against V01 and `main...c875c523`.
- Verdict: **PASS_WITH_NOTES** at source level. There are no blockers and H1 is resolved.
- Compile/XCTest on c875c523: **NOT_VERIFIED**. At review time `gh run view 44747483502` showed status=queued for headSha c875c523. CI is the only Swift compiler. Acceptance requires both of the following:
  - "Unsigned iOS Simulator build and XCTest" passes with exactly 222 tests, 0 failed and 0 skipped.
  - "Unsigned iOS device archive" is green.
- The run on e6ba1860 (Simulator XCTest 222 PASS) is the coordinator's report. I did not re-check it myself.

## V01 findings: resolution status
- **H1 (in-flight duplicate sequence): RESOLVED.**
  - Fix: ContentView.swift:521-524. The check-and-set of `manualCaptureInFlight` runs synchronously on the MainActor before the first `await`, and `defer` clears it on every return path.
  - The button is disabled while in flight (:979).
  - `requestManualCapture` is the only UI capture entry. The other `storeAcceptedCapture` callers at :619/:628/:642/:655/:784 have no UI caller.
  - Regression test: PackLabCaptureTests.swift:3244-3268. It runs two overlapping `async let` taps. It then checks distinct record sequences equal to 0..<n, the acceptedIDs set and count, and that `nextSequence` equals n. That check catches the duplicate-sequence outcome even in the case where both taps are allowed, so the test is not tautological.
- **M1 (photos.json outside the txn): PARTIALLY RESOLVED.** ContentView.swift:486-495 now rolls back a failed append via `SessionGalleryStore.delete`. Notes:
  - (a) **No test** injects an append failure, so the rollback path is unexercised.
  - (b) If photos.json is corrupt, which was one of the V01 triggers, `rewritePhotoMetadata` throws inside `delete` (SessionFoundation.swift:385). The `try?` then swallows that and the committed record remains. The session is unfinalizable anyway in that case.
  - (c) The rollback writes a gallery audit event `action: "delete"`, so a system rollback is indistinguishable from an operator delete in the audit trail.
  - (d) The crash-window gap is acknowledged with a `ponytail:` comment.
- **M2 (gallery delete/retake photos.json): RESOLVED.**
  - Fix: SessionFoundation.swift:343-345 and :364-375, inside `mutate`, whose backup and restore covers photos.json. When photos.json is absent, the restore correctly removes any file created by the failed operation.
  - Retake metadata is honest. Dimensions are decoded from the replacement bytes, orientation is labelled `.derived`, and focal length, exposure, ISO and white balance are all `.unavailable`. No camera values are fabricated.
  - Test :3236-3271 finalizes after delete and after retake.
  - Edge: a retake whose old ID is absent from photos.json leaves the replacement unlisted (legacy sessions only).
- **M3 (2 Hz log evicts manual audits): NOT ADDRESSED.** This was non-blocking in V01 and remains an open follow-up.
- **M4 (stale evidence): RESOLVED.**
  - Fix: ContentView.swift:531-534. Evidence older than 2.0 s blocks with `live_frame_stale`, and a non-finite age also blocks.
  - Minor: a negative age (evidence timestamp after the request) passes the check. That is harmless in the uptime domain.
  - Tested at :3238-3240.
- **L1: RESOLVED** at :135, where `start()` restarts the loop when coverage is active.
- **L2: RESOLVED.**
  - `endActiveSession` (:546-554) is wired to finalize (SessionFoundation.swift:899, `onFinalized`) and to discard (ContentView.swift:1041, called before deletion). It is guarded by session ID.
  - Residual: an already in-flight tick or manual capture holds its own layout and could still land one write after `endActiveSession`. This is LOW.
- **L3: RESOLVED.** The instance-level `liveCandidateSequence` is never reset (:85 and :596-597), and the test checks it is monotonic.
- **L4–L8:** unchanged and acceptable, as noted in V01.

## New-change checks
- **Swift 6 / concurrency:**
  - `onFinalized` and `onManualCaptureFrame` are `@MainActor` closures.
  - `ButtonFrameRecorder` is `@MainActor`.
  - The `async let` calls on the MainActor VM are fine.
  - `analyzeM04Candidate(... frame:)` in the layout test relies on `pose:` defaulting to nil (ContentView.swift:426), which it does.
  - I see no new compile risk, but this is pending CI.
- **Layout (c875c523):**
  - The live quality readout is now inside the `.frame(maxHeight: 320)` ScrollView (:911-969). The manual block reasons sit below the button, so they cannot push it down.
  - The test (:3302-3333) now fills in `m04Evaluation` and manual blocking reasons before asserting `safeArea.contains(buttonFrame)`.
  - Limits:
    - It is iPhone 16 Simulator geometry only.
    - It is not a hit-test or occlusion proof. In the e6ba1860 screenshot the button overlaps the Simulator "Camera unavailable" placeholder text.
    - That screenshot predates c875c523, so it does not show the worst-case readout.
- **Workflow:**
  - upload-artifact is pinned to 043fb46d... (# v7.0.0), the same SHA used across the repo.
  - `retention-days: 3`.
  - The export step has no `if:`, so it runs only after the count gate succeeded. A failed export writes EXPORT_FAILED.txt and does not mask a test failure.
  - No secrets are referenced.
  - The iOS 18.0 platform step is an exact copy of the existing Simulator-job guard (lines 360-372), including the final `has_runtime` check that fails closed.
  - Residual: if `-downloadPlatform iOS` fetches a non-18.0 runtime, the step fails loudly rather than silently. That is acceptable.
- **Count guard:** `func test` count is 222 at head and 217 on main. The +5 tests are the 3 from V01, the gallery delete/retake test and the layout test. The workflow `all) expected=222` matches exactly, and no other Swift test files exist.
- **Authority and safety:** QualityDecisionPolicy, M04 thresholds and the hard blocks are unchanged. The new blocks (`capture_in_flight`, `live_frame_stale`) only add refusals.

## Local evidence (reviewer-run)
- `python -m pytest tests/packscan/test_ios_row_button_styles.py tests/packscan/test_swift_authoritative_contracts.py tests/ci -q` gave 424 passed, 7 skipped and 4 failed. All 4 failures are in tests/ci/test_packlab_test_runner_behavior.py (disk-budget runner tests), which is the known local-only flake. There were no other failures.

## Recommended follow-ups (non-blocking)
1. Add an M1 rollback test that injects an append failure (for example a pre-existing duplicate photo ID). It should assert no record or source remains, acceptedIDs is unchanged, and the result is `capture_persist_failed`.
2. Give the rollback a distinct audit action (for example `rollback`) instead of `delete`.
3. Address M3 by moving manual audits to their own log, or by de-duplicating unchanged candidate rows.
4. Real-iPhone acceptance (layout on a physical device, live loop with real ARFrames) remains a separate owner gate. This review makes no device claim.
