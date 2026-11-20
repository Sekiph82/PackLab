# CLAUDE_PEER_REVIEW - iOS capture guidance (PR 8) V02 re-review

- Reviewer: Claude (independent source reviewer; did not author this change)
- Branch / head: feat/ios-capture-guidance at 69913ee83c322a25219ca0ab38a3eb428d791a99
- Diff reviewed: git diff 4671297e..69913ee8 (5 files, +325/-53), with the full PR where needed
- Verdict: PASS_WITH_NOTES for source. CI NOT_VERIFIED: gh pr checks 8 showed Locked Python quality, the Simulator build+XCTest and the device archive as pending. The signing-material scan passed. Swift 6 compilation and the 230-test run are not yet proven.

## Blockers
None in source. Merge still requires green CI (all=230).

## V01 findings: status
- M1 (dead raycast tiers): RESOLVED. ARTrackingService.swift:98 sets planeDetection = [.horizontal]. Lines 199-206 query all three tiers with alignment .horizontal. worldAlignment is not set anywhere in apps/ios-capture, so the default .gravity applies and world +y is up.
- M2 (center behind the package): RESOLVED in design. The crosshair now targets the base point and ObjectCenterBuilder (M04CaptureEngine.swift:749) lifts it along world +y by h/2. The 1.5 m / 0.1 m / cos 15 deg = 0.966 checks are correct, and the test pins both sides of 15 deg (10 deg passes, 20 deg is rejected). Using worldTransform.columns.1 as the normal follows the ARKit convention that a plane's y-axis is its normal. Because every query is .horizontal-aligned, this check is mostly redundant; a wrong axis would cause a false rejection, never a false acceptance. New residual issue: see N1.
- M3 (cross-world coverage): RESOLVED. On a world change, validateObjectCenterWorld (ContentView.swift:~684) calls restartCoverageForNewWorld (:695). That moves the old snapshot into previousWorldCoverage, which is persisted (:850) and never fed into m04RingCoverage or completion, and resets the orbit, base and detail models. Resume and legacy restores are flagged the same way (:664). Each observation records frameID (the center's worldIdentity, or nil for world-origin observations). Tests cover live reset, persistence, relaunch resume and legacy restore. Residual issues: see L1 and L2.
- L4 (unaudited refusals): MOSTLY RESOLVED. refuseManual (:710) logs a QualityCandidateLog with manualAudit, and the test asserts this. A refusal is still not logged when no candidate evaluation exists (:712); the code comment documents this.
- L5 (lower ring) / L6 (turntable toast): RESOLVED. The texts are updated and the protocol line is added. The turntable toast is gated by orbit: preset != .turntable and is tested.
- L7: unchanged (it was acknowledged).

## New findings (mine)
### MEDIUM
N1. The infinite-plane tier is tried before the estimated plane (ARTrackingService.swift:200-202). If the floor has been detected but the table has not, existingPlaneInfinite can hit the extended floor plane under the table. The center would then be about 0.7 m too low. The 1.5 m distance check rejects shallow aims (about 1.75 m path length) but accepts steep ones (60 deg depression gives about 1.15 m). The method string records the tier honestly. Suggested fix: try estimatedPlane before existingPlaneInfinite, or reject hits more than about 0.6 m below the camera. Needs device validation. Not a gate or honesty problem.
N2. The package-height provenance on resume can be wrong. The new-scan path sets the type default (ContentView.swift:1278), but configureM04QualityRuntime (:193) does not reset packageHeightMeters/packageHeightSource and the resume path (:1284) never sets them. After a relaunch, resume therefore shows the .other default of 15 cm labelled as the type default, even when the package is a bottle (20 cm). Within one app run, resuming scan B after scan A carries A's height as "operator_entered", and that value is written into B's ObjectCenter.heightSource. This is a traceability problem: the label claims an operator entry that never happened. Suggested fix: on resume, use context.objectCenter's height and source if present, otherwise PackageHeightDefaults.meters(for: draft.packageType); or reset both in configureM04QualityRuntime. This is a recommended pre-merge fix. It does not block, because the value is shown on screen, the operator can edit it, and it affects guidance only, not metric output.

### LOW
L1. Only the most recent previous world is kept. restartCoverageForNewWorld (:696) overwrites m04PreviousWorldCoverage, and restoreObjectCenter sets the persisted value first and then restart overwrites it. Earlier worlds therefore drop out of the context. Per-photo pose bindings remain, so this is not data loss of photos.
L2. Turntable resume clears the world-origin ring, base and detail coverage into previousWorldCoverage (restoreObjectCenter with center == nil and non-empty coverage). A mid-session tracking reset does not do this, because a turntable session has no center. The "Earlier AR session" text is only rendered inside the orbit-guidance block, so turntable operators do not see it. The behaviour is conservative (nothing is overcounted), but it is inconsistent and should be documented.
L3. Every automatic tracking-degraded reset now restarts all orbit coverage. That is honest, but on low-texture tables it may be costly. Device UX validation is needed.

## Layout test fix (CI 1/228 on 4671297e)
This is legitimate and not masking a bug. updateOrbitGuidance maps the live pose from `pose`, which is only populated by refresh(). Before the first refresh the observation is pose_unavailable. In production, start() runs from ContentView's .task, refresh() is polled every 100 ms, and the dial simply shows no dot for that one tick, which is acceptable to the user. The test now calls vm.start() (with automaticallyPoll false, so one refresh). It asserts the exact sector (middle, 6), which matches 270 deg, and waits for sector != nil. That is stronger than before, not weaker.

## Gates / thresholds
ManualCaptureCoordinator, QualityDecisionPolicy and AutoCaptureController are untouched. No threshold was relaxed. The world-change refusal reuses object_center_unset. The workflow change is only expected 228 -> 230.

## Compile-risk review (CI is the only compiler)
No definite error found. Items checked:
- simd_float4 columns.1/.3 .x/.y/.z
- Result<ObjectCenter, ObjectCenterRejection> with a String-raw Error enum
- nested string literals in the Text interpolation (valid since Swift 5)
- `return (await refuseManual(...), nil)` (await inside a tuple element is valid)
- the @discardableResult Bool from validateObjectCenterWorld called as a statement
- `guard case ... else { return XCTFail(...) }` in a Void test

## Tests / counts
- grep -c "func test" PackLabCaptureTests.swift = 230. The workflow has all) expected=230. Exact match.
- The new tests (builder plausibility and lift, world change / resume / legacy, refusal audit, height edit provenance, turntable toast) assert numeric and state outcomes and are not tautological.
- Local run: pytest on tests/packscan/test_ios_row_button_styles.py, tests/packscan/test_swift_authoritative_contracts.py and tests/ci gave 424 passed, 7 skipped and 4 failed. All 4 failures are in tests/ci/test_packlab_test_runner_behavior.py, the known local flake.
