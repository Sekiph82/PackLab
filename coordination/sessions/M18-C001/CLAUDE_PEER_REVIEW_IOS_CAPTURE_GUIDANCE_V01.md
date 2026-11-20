# CLAUDE_PEER_REVIEW - iOS capture guidance (PR 8) V01

- Reviewer: Claude (independent source reviewer; did not author this change)
- Branch / head: feat/ios-capture-guidance at 4671297e85b0b86cbb009e3cec8ef99c388e4c35
- Diff: git diff origin/main...origin/feat/ios-capture-guidance (6 files, +802/-49)
- Verdict: PASS_WITH_NOTES for source review. CI NOT_VERIFIED: when this review was written, the iOS Simulator build+XCTest, the device archive and Locked Python quality checks were still pending, so compilation (Swift 6, warnings-as-errors) and the 228-test run are not yet proven.

## Blockers
None found in source. Accepting the PR still requires green CI (expected=228).

## Findings

### MEDIUM
1. The raycast fallbacks can never fire. See PackLabCapture/Services/ARTrackingService.swift:193-208 and :96. DeviceARSessionDriver.run builds an ARWorldTrackingConfiguration but never sets planeDetection, which defaults to empty. With no ARPlaneAnchors, the existingPlaneGeometry and existingPlaneInfinite attempts cannot hit anything. Only estimatedPlane works, so the three-tier fallback in the doc comment describes code that never runs. The fix is either to enable horizontal plane detection (this costs heat) or to remove the dead tiers and correct the comment.
2. The object center can be badly wrong for some materials. For transparent or glossy PET, or any thin package, the screen-centre ray often misses the package and hits the mat or table behind it. Worked example: camera 25 cm above the table, 35 cm away, aimed at the mid-height of a 20 cm bottle. The ray reaches the table about 23 cm behind the bottle. Azimuth and elevation are then measured around a point that is not the package, so guidance is wrong. Elevation is also biased upward: with the center at table height, the lower ring would need the camera below the tabletop. Matte packages have a smaller bias of the same kind: the hit is on the front face, about half the package depth toward the camera (approx. 3-4 cm, under 6 deg azimuth at 35 cm), which is acceptable for 45 deg bins. Nothing checks whether the hit is plausible, for example its distance against the framed object or its height against the table plane. The method is recorded truthfully (raycast_estimated_plane), so this is a quality problem, not an honesty one. It should be resolved before any physical-validation claim.
3. Coverage frames are mixed after an AR world change. This is pre-existing, not a regression. validateObjectCenterWorld and restoreObjectCenter (ContentView.swift:630-648) correctly drop the center. However, the restored or accumulated m04Coverage sectors stay. Their azimuth zero is -z of the old world, which is the camera heading when that world started, and a new world has an unrelated heading. Two things trigger this: the automatic trackingDegraded reset after 3 limited frames, which re-runs with resetTracking, and any resume after relaunch, which creates a new ARSession identifier. Sectors from different frames then count toward completion. Persisted observations also do not record which center or world they were measured in, so legacy world-origin observations and object-centred observations cannot be told apart. Recommended follow-up: add center/world provenance per observation or snapshot, and invalidate or flag cross-world coverage.

### LOW
4. Refused attempts are not audited. object_center_unset refusals (ContentView.swift:566) return before captureAndPersistManual, so no QualityCandidateLog entry with manualAudit is written. session_not_ready and live_frame_stale already behave this way. Attempts that reach the coordinator are still audited (ContentView.swift:496). The heat change (recordDiagnostics false, ContentView.swift:437 and :718) removes only the 2 Hz live-frame log lines; no downstream consumer of the live log exists in the app. The test asserts the live log is empty. The context is still persisted on accepted captures via recomputeM04Completion and scheduleM04ContextPersistence, and on guidance-state change.
5. The lower ring is hard to reach in practice. Elevation is atan2(cam.y - center.y, r), positive above the center, so the raise/lower signs match the rings (lower -35..-10, middle -10..15, upper 15..40). With the center at mid-height of a 20 cm bottle and r approx. 35 cm, the lower ring needs the lens 6-25 cm below mid-height. In practice that means the phone almost resting on the table, and the -35 deg end is unreachable on a tabletop. Short packages (under approx. 12 cm) cannot reach the lower ring on a table at all. This review does not require changing the thresholds. The protocol text should tell the operator to hold the phone at table level or place the package near the table edge, or the lower ring should be treated as conditional in UX text.
6. The toast has layering and turntable issues. It calls ContentView.manualBlockHint from the view model, which is a minor layering smell. For a turntable preset with manual capture, observations fall back to world-origin mapping, and the toast may say the wedge is already covered or ask for the object center, which is misleading.
7. Thumbnail decoding runs on the main actor (SessionFoundation.swift:1015 and :1030). This is acknowledged with a ponytail comment. ImageIO downsampling (300 px thumbnails, 2048 px full screen, CreateThumbnailWithTransform) keeps memory bounded.

## Geometry re-derivation (independent)
- ARKit world is right-handed and y-up; at session start the camera looks along -z and x is to the right. Azimuth is atan2(x, -z) of camera minus center, which increases clockwise when seen from above.
- Example: operator at (0,0,1), azimuth 180 deg, facing -z, so their left is -x. Stepping to (-e,0,1) gives atan2(-e,-1), just above 180 deg, so walking left increases azimuth. Correct, and it matches the instruction (positive delta means walk left).
- dialScreenAngle = az - current + 180, clockwise from the top with y down, and the unit vector is (sin, -cos). The current position is at the bottom. A target at current+d gives a screen angle of 180+d, so x = -sin d < 0, which is screen-left. The top view maps clockwise to clockwise with no mirror. Correct.
- nextTarget, signedDelta and the 0/360 wrap all check out. The walk-degrees rounding is consistent with the test (32.5 gives 35).

## Gate / honesty checks
- ManualCaptureCoordinator, QualityDecisionPolicy and AutoCaptureController are not in the diff. The only new gate is object_center_unset, which is skipped for turntable. No existing gate is weakened. overlapAllowed semantics are unchanged because the target is always a missing sector.
- ObjectCenter records position, method, worldIdentity (session identifier plus epoch) and setAt. Tests use test_injected and test_raycast method strings, so no fabricated device evidence is presented as real. M04ScanContext.objectCenter is optional, and a legacy decode is tested. Resume restores the center only when the world identity matches, so after a relaunch it is always re-set.
- The photo viewer is read-only: it has no delete, share or Photos-library API. It lists only state.acceptedIDs that have a record and an existing source, and the orphan exclusion is tested. The View photos button is borderless in the List row, and test_ios_row_button_styles.py passes.

## Compile-risk review (CI is the only compiler; NOT_VERIFIED until green)
These checked out on reading:
- ARFrame raycastQuery(from:allowing:alignment:) takes normalized image coordinates, so 0.5/0.5 is the centre regardless of orientation and aspect-fill crop.
- ARSession raycast and ARSession identifier (UUID, iOS 13+) exist.
- Canvas uses a capture list of value types, and the nested point func does not capture the inout context.
- Image(decorative:scale:) and fullScreenCover(item:) with an Identifiable item are fine.
- MainActor-typed closures that capture the MainActor TestARWorld are fine.
- ForEach over the Identifiable CoverageRingDefinition is fine.
- The project is iOS-only (SDKROOT iphoneos).

No definite compile error was found.

## Tests
- Count guard: grep -c "func test" gives 228 on the head and 222 on origin/main; the workflow expects all=228. Exact match.
- The new tests are not tautological:
  - The mapper test pins a numeric world-origin vs object-center difference.
  - The gate test covers unset, set, world change and resume in the same and a different world.
  - The photo index test covers order, orphan exclusion and labels.
  - The dial/instruction consistency test uses the same convention on both sides, so it does not prove the ARKit handedness. The re-derivation above covers that.
- Local run: pytest on tests/packscan/test_ios_row_button_styles.py, tests/packscan/test_swift_authoritative_contracts.py and tests/ci gave 424 passed, 7 skipped and 4 failed. All 4 failures are in tests/ci/test_packlab_test_runner_behavior.py, which the caller identified as a local flake.
