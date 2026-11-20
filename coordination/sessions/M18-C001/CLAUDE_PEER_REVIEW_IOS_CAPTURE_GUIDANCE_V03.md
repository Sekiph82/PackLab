# CLAUDE_PEER_REVIEW - iOS capture guidance (PR 8) V03 delta review

- Reviewer: Claude (independent source reviewer; did not author this change)
- Branch / head: feat/ios-capture-guidance at e325001599bfa8a13aca884d11056e46ec9d647d (matches origin after fetch)
- Diff reviewed: git diff 69913ee8..e3250015 (5 files, +83/-9)
- Verdict: PASS_WITH_NOTES for source. CI NOT_VERIFIED: gh pr checks 8 shows Locked Python quality, the Simulator build+XCTest and the device archive as pending. Only the signing-material scan has passed. Neither Swift 6 compilation nor the 231-test run is proven yet.

## Blockers
None in source. Merge still requires green CI (all=231).

## V02 findings: status
- N1 (floor hit from the infinite-plane tier): RESOLVED.
  - ARTrackingService.swift:201-205 now queries existingPlaneGeometry, then estimatedPlane, then existingPlaneInfinite.
  - As a backstop, ObjectCenterBuilder (M04CaptureEngine.swift:747, :759) rejects hits more than 0.6 m below the camera (cameraPosition.y - position.y), returning .tooFarBelow ("base_point_too_far_below", :711) with an operator message (:720).
  - The check sits after tooFar/tooNear and before notHorizontal. Existing test rows are unaffected: the tooFar row (drop 0.8) is still caught first by distance, and the other rows have drops of 0.3 or 0.35.
  - The boundary test (PackLabCaptureTests.swift:3525-3526) pins both sides of the limit (drop 0.59 passes, 0.61 is rejected) against the hit() helper's camera at y=0.3 (:3504).
  - The ARKit world uses .gravity alignment (V02), so y is up.
- N2 (package height carried across scans/resume): RESOLVED.
  - configureM04QualityRuntime now resets height and source (ContentView.swift:230-231).
  - beginScan (:237-240) applies the package-type default. It is used by both New Scan (:1290) and Resume (:1296), and these are the only non-test callers of configureM04QualityRuntime, so no mid-session path wipes an operator height.
  - restoreObjectCenter (:676) adopts the stored height and source in any world, but restores the center only when the world matches (:677-679). The cross-world center is not restored.
  - Provenance is honest: a carried value keeps its original "operator_entered" or "package_type_default" source, and a missing recorded height falls back to the type default.
- L2 (turntable resume vs reset): RESOLVED. In restoreObjectCenter (:684), a turntable preset skips restartCoverageForNewWorld and the "new AR session" message. This matches the mid-session reset path, which is a no-op for turntable because it has no center. The test asserts that restored coverage keeps 1 sector and that previousWorldCoverage stays nil.

## Test
- testPackageHeightIsNotInheritedBetweenScansAndResumeUsesRecordedHeight (PackLabCaptureTests.swift:3597-3646) is not tautological. Each block would have failed before this change:
  - The bottle 0.25 operator value leaked into the jar scan.
  - A cross-world recorded height was dropped.
  - Turntable coverage was moved to previous-world.
- Helpers and signatures exist: acceptedPoseBinding :96, orbitPose :137, bindObjectCenterSources ContentView.swift:619, ObjectCenter init M04CaptureEngine.swift:694, PackagingPresetCatalog.turntable :1243.
- Count guard is exact: `grep -c "func test"` in PackLabCaptureTests.swift = 231, and the workflow has all) expected=231 (packlab-capture-macos.yml:597). No other test file defines tests.

## Swift 6 strict risk
Low. beginScan is a method on the same @MainActor view model and is called from the same SwiftUI closures that previously called configure and setPackageHeight. The new enum case is handled in the exhaustive `message` switch. The `if a, b || c` condition is valid. The test is @MainActor async. CI is still needed to prove it.

## Notes (non-blocking)
- N1' (heuristic): the 0.6 m drop limit is a calibration knob. A low table or a high overhead hold can exceed it: a 45 cm coffee table with the phone at about 1.15 m gives a drop of about 0.7 m and would be refused. The message tells the operator why. Revisit with real-device evidence.
- L1: restoreObjectCenter (ContentView.swift:676) assigns the persisted height without the finite check and range clamp that setPackageHeight applies (:627-628). A corrupt stored value would surface later as .invalidHeight, not a crash or a bad center. Routing it through the same clamp would be cleaner.
- L2': after a cross-world resume, the recorded height lives only in the runtime (m04ObjectCenter is nil, and height is persisted only inside the center). If the app relaunches again before the center is re-set, the height falls back to the type default with an honest source.

## Local evidence (reviewer-run)
`python -m pytest tests/packscan/test_ios_row_button_styles.py tests/packscan/test_swift_authoritative_contracts.py tests/ci -q`: 424 passed, 7 skipped, 4 failed. All 4 failures are the known local flakes in tests/ci/test_packlab_test_runner_behavior.py (3 tiny-budget params plus measurement_exception).
