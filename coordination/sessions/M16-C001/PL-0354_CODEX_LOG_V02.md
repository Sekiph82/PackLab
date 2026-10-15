# PL-0354 Codex Log V02 — R01 Swift/XCTest recovery

## Result

**Implementation published to private `main`; focused recovery XCTest passed 25/25. The required full 205-test hosted run is blocked before runner startup by GitHub account billing/spending-limit enforcement. This is not `READY_FOR_INDEPENDENT_AUDIT`.**

Current handoff: `BLOCKED_HOSTED_CI_BILLING / FULL_XCTEST_NOT_EXECUTED / AWAITING_AUDIT`.

## Authority and synchronization

- Repository: `Sekiph82/PackLab`, confirmed private on 2026-10-15.
- Task: PL-0354-R01 only. Read the live `TASKS.md` status, the R01 prompt, original PL-0354 prompt and criteria, V01 log, V01 independent audit, cleanup addendum, root `AGENTS.md` policy, and relevant historical PL-0073/0080/0102/0104/0105/0106/0109/0120/0121 contracts.
- Starting worktree commit: `d5de96651d17563cd41eb2ffbfe93ff23018f2d2`.
- While preparing the isolated task worktree, `origin/main` advanced to `a06b7f923bbee75bc1680d8c7563450c03f4cde7` to publish the auditor's V01 result and the R01 prompt. Fetched and fast-forwarded safely; the intervening changes did not overlap the task source files.
- Final implementation commit: `4b1cf5168c6a2c461e4b31735763393c5ea0f53c`, fast-forwarded to `main`. The V02 log is published separately in its own commit (recorded after push below).
- No reset, rebase, force push, stash, or Desktop checkout changes.

## Actual hosted evidence

All successful hosted runs used `macos-15`, Xcode 16.0 (16A242d), macOS 15.7.9, iOS Simulator SDK 18.0, iPhone 16 / iOS 18.0. The runner resolved the pinned NextLevel **0.19.1**. App builds used `CODE_SIGNING_ALLOWED=NO`, `CODE_SIGNING_REQUIRED=NO`, and an empty `CODE_SIGN_IDENTITY`.

| Run | Revision / selection | Actual result |
| --- | --- | --- |
| [38755083949](https://github.com/Sekiph82/PackLab/actions/runs/38755083949) | V01 baseline `c9c0a1c66138c7cbd07bd889cf956fad415c96dd`, full suite | App build PASS; 205 XCTest total, 173 passed, 32 failed, 0 skipped; job failed as required. This is the prior audited result, not R01 success. |
| [38762546093](https://github.com/Sekiph82/PackLab/actions/runs/38762546093) | `c1acce8a`, focused session group | Build stopped on a Swift 6 actor-transfer diagnostic for injected `FileManager`; fixed with a narrow wrapper preserving injection. No XCTest ran. |
| [38763502299](https://github.com/Sekiph82/PackLab/actions/runs/38763502299) | `888b8c6d`, session group | Unsigned app build PASS; 7 tests, 6 passed, 1 failed (two manifest assertions in that test). Corrected the synthetic manifest to satisfy the production contract before testing its intended checksum/binding failures. |
| [38765301242](https://github.com/Sekiph82/PackLab/actions/runs/38765301242) | `3f6a2e24`, `recovery_all` | Unsigned app build PASS; 25 tests, 21 passed, 4 failed, 0 skipped. Diagnosed those four; no assertion was weakened. |
| [38767357450](https://github.com/Sekiph82/PackLab/actions/runs/38767357450) | `ce422ebf`, `recovery_all` | **PASS**. Unsigned app build PASS; xcresult `Passed`, 25 total, 25 passed, 0 failed, 0 skipped; job success. This exercised all 25 distinct test methods identified in the original 32-failure hosted report. |
| [38768830642](https://github.com/Sekiph82/PackLab/actions/runs/38768830642) | `ce422ebf`, canonical `main` push / full suite | Unsigned app build PASS; XCTest did not start because the default `all` path referenced an uninitialized Bash array under `set -u`. No xcresult was produced. Fixed and pushed the selector initialization. |
| [38770566255](https://github.com/Sekiph82/PackLab/actions/runs/38770566255) | `4b1cf516`, canonical `main` push / full suite retry | GitHub did not start the job or allocate a runner. Annotation: “The job was not started because recent account payments have failed or your spending limit needs to be increased.” No build or XCTest ran. This is the current blocker; no payment/billing settings were changed. |

The focused selector includes these 25 original failing test methods; all passed on run 38767357450:

- `testAuthoritativeDeletionRemovesSessionAndRejectsTraversal`
- `testDeletionPlanRequiresConfirmationAndStaysInsideRoot`
- `testFinalizationGateDistinguishesBindingAndChecksumFailures`
- `testPL0073FocusCannotLockBeforeObservedStabilization`
- `testPL0080AndPL0081AcceptedStillOrchestrationPersistsPoseMotionAndReopens`
- `testPL0083AndPL0085RuntimeRefreshUsesInjectedServicesAndStops`
- `testPL0085OverlayPropagatesNewestPoseMotionAndEpochThenStops`
- `testPL0088EveryTransactionFailureStageRecoversCleanPreCaptureState`
- `testPL0089RetakeCallbackAndDeleteRetakeFailureStagesRollbackCoherently`
- `testPL0090DiscoveryUsesRecoveredStateBlocksCorruptionAndDiscardsOnlyResumableSessions`
- `testPL0095CandidateRuntimePublishesAlignedMotionWarningsAndHighRisk`
- `testPL0097CandidateRuntimePublishesShadowBandsAndRawObjectFraction`
- `testPL0102CoverageUsesExactElevationBoundariesAndAdjacentValuesDeterministically`
- `testPL0104ProductionAutoCaptureUsesHealthGatedBackendAndAcceptedTransaction`
- `testPL0104ProductionGateMatrixNeverInvokesBackendWhenBlocked`
- `testPL0105DuplicateDetectorProvesTranslationElevationAndSignatureBoundaries`
- `testPL0106RingAndSectorBoundariesAreDeterministicInLiveGuidance`
- `testPL0109ActiveCompletionPropagatesAndPersistsWithOptionalBaseState`
- `testPL0109CompletionDiagnosticsDistinguishesCompleteAndUnavailableEvidence`
- `testPL0118PreflightIsTableDrivenAcrossPresetsAndHealthConditions`
- `testPL0120ProductionSharePresentationStateCoversCancelCompletionFailureAndReplacement`
- `testPL0120ShareEligibilityRejectsMissingOrNonPackscanFiles`
- `testPL0121SwiftWireModelsMatchSharedGoldenFields`
- `testPoseClockBridgeBindsAcceptedStillAndExactBoundaries`
- `testSessionDiscoveryReconstructsHistoryAndBlocksMissingOrVersionMismatch`

The original result reported 32 failed assertions across 25 distinct test methods. These counts are preserved separately; they are not described as 32 distinct test methods. The 180 test methods outside this focused recovery selection have **not** been re-executed on the final revision.

## Changes published

- `.github/workflows/packlab-capture-macos.yml`: Added bounded manual focused selection and exact per-selection xcresult count, failure, skip, and result gates; kept the push/PR default on the complete 205-test suite. Initialized the selector arrays so the default full path works under `set -u`. No skip list, ignored failures, relaxed count, or signing path.
- `apps/ios-capture/PackLabCapture/ContentView.swift`: Added deterministic polling control for injected runtime tests; serialized M04 context writes and exposed an awaitable persistence completion point for tests.
- `apps/ios-capture/PackLabCapture/Services/CameraFoundation.swift`: Preserved the injected file manager through the source-store actor boundary; premature/unsupported focus locking reports failure without corrupting the prior focus state.
- `apps/ios-capture/PackLabCapture/Services/M04CaptureEngine.swift`: Corrected floating-point boundary handling for ring/elevation and duplicate thresholds; cooldown uses the accepted request timestamp domain.
- `apps/ios-capture/PackLabCapture/Services/PackScanShareSheet.swift`: Detects a missing/replaced package using fresh file attributes.
- `apps/ios-capture/PackLabCapture/Services/SessionFoundation.swift`: Cleans only an unmarked, pre-commit transaction directory; restores previously absent gallery paths on rollback; checks resolved deletion containment before authority classification; persists the accepted record with its newly bound pose/motion evidence.
- `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift`: Corrected synthetic protocol, resumable-session, finalization-manifest, focus, pose timing, image-quality dimensions/fractions, auto-capture timestamp, duplicate-signature, and persistence-wait setup while keeping safety and behavior assertions intact.

## Commands and expected results

- Workflow static validation: parsed `.github/workflows/packlab-capture-macos.yml` with PyYAML and ran `bash -n` against each embedded shell script. Expected valid YAML and shell; actual PASS after the final selector initialization.
- `git diff --check` before each implementation commit: expected no whitespace errors; actual PASS.
- Focused hosted command: `xcodebuild test -project apps/ios-capture/PackLabCapture.xcodeproj -scheme PackLabCapture -destination 'platform=iOS Simulator,name=iPhone 16,OS=18.0' ... CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY=''` with `-only-testing:PackLabCaptureTests/PackLabCaptureTests/<testName>` for all names in `recovery_all`. Expected 25 selected, all passing; actual PASS on run 38767357450.
- Full hosted command uses the same project, scheme, destination, and unsigned settings without `-only-testing`. Expected exactly 205 total, `Passed`, zero failures/skips, and successful job. Actual: not executed because run 38770566255 was blocked before runner allocation by GitHub billing enforcement. The prior full run remains 173/205 and failed; it has not been overwritten or reclassified.
- No local XCTest substitution, Windows Installer/OCCT/OCP build, signed build, physical-device test, or private sample scan was used.

## Privacy and limitations

- Repository privacy checked as `private=true` before publication.
- No Apple signing material, GitHub token, scan/image, owner data, or xcresult artifact was committed or uploaded. Hosted runs retained only aggregate text summaries in GitHub Actions.
- NextLevel remains exactly 0.19.1. The runner-local Swift 5 compatibility adjustment is restricted to the resolved dependency manifest on the ephemeral runner; dependency source and repository pin were unchanged.
- The original 25 failing test methods pass in hosted focused execution. The full 205-test suite on final `main` remains unverified because the GitHub account blocked the retry before a runner started. No claim of full-suite PASS or task completion is made.

## Publication and handoff

- Implementation pushed to private `origin/main` through fast-forward commits, final implementation SHA `4b1cf5168c6a2c461e4b31735763393c5ea0f53c`.
- Focused green evidence: https://github.com/Sekiph82/PackLab/actions/runs/38767357450
- Full canonical retry blocked before runner startup: https://github.com/Sekiph82/PackLab/actions/runs/38770566255
- Root `TASKS.md`, ChatGPT audit files, PL-0355, and M17 were not edited or started.
- Post-task worktree cleanup will occur only after this log commit is published, per the cleanup addendum. Its measured result will be reported to the user after cleanup.

**BLOCKED_HOSTED_CI_BILLING / FULL_XCTEST_NOT_EXECUTED / AWAITING_AUDIT**
