# PL-0354 Codex Log V01

## Status

**Verification blocked; do not mark READY_FOR_INDEPENDENT_AUDIT.** The hosted iOS Simulator app build passed, and real XCTest execution completed, but the existing `PackLabCaptureTests` suite reported 32 failures. The workflow correctly returned nonzero. These failures span existing session storage/deletion/finalization, camera-control, capture/coverage, and transfer behaviors outside this CI task's frozen implementation scope. No assertions or tests were removed or weakened to obtain a green result.

## Commits and synchronization

- Starting commit: `e164032930374768dc295542e83915ac30bcd8bc`.
- Final implementation commit: `c9c0a1c66138c7cbd07bd889cf956fad415c96dd`.
- Synchronization: fetched private `origin/main`; the implementation worktree matched `origin/main` before the log commit. Implementation commits were pushed to `main` without force; no `TASKS.md` edit was made.
- Prompt read: `coordination/sessions/M16-C001/PL-0354_CODEX_PROMPT_V01.md`.
- Criteria read: `coordination/sessions/M16-C001/PL-0354_CHATGPT_AUDIT_CRITERIA_V01.md`.
- Cleanup addendum and permanent root `AGENTS.md` worktree lifecycle policy read and applied.

## Implementation

- Added `.github/workflows/packlab-capture-macos.yml`: `macos-15`, explicitly selected Xcode 16.0, iOS 18.0 Simulator runtime and iPhone 16 destination, least-privilege `contents: read`, bounded job timeout, relevant push/pull-request triggers and manual dispatch.
- Workflow runs unsigned `xcodebuild build` and `xcodebuild test` for the existing `PackLabCapture` scheme; signing is disabled with `CODE_SIGNING_ALLOWED=NO`, `CODE_SIGNING_REQUIRED=NO`, and empty `CODE_SIGN_IDENTITY`.
- Added a shared Xcode scheme for the existing app and `PackLabCaptureTests` targets. Added the missing `CFBundleExecutable=$(EXECUTABLE_NAME)` app plist entry required for Simulator installation. Set Debug Swift optimization to `-Onone` for app and test targets.
- Preserved the exact NextLevel `0.19.1` project pin. The workflow applies a checked, runner-local Swift 5 language-mode compatibility adjustment to the resolved NextLevel manifest; dependency source and repository pin remain unchanged.
- Resolved Swift 6 compile blockers in existing iOS app and test sources so the simulator targets compile. The tests were not weakened to suppress runtime failures.
- Files changed by the PL-0354 implementation: `.github/workflows/packlab-capture-macos.yml`; `apps/ios-capture/PackLabCapture.xcodeproj/project.pbxproj`; `apps/ios-capture/PackLabCapture.xcodeproj/xcshareddata/xcschemes/PackLabCapture.xcscheme`; `apps/ios-capture/PackLabCapture/ContentView.swift`; `apps/ios-capture/PackLabCapture/Info.plist`; `apps/ios-capture/PackLabCapture/Services/ARTrackingService.swift`; `CameraFoundation.swift`; `CameraService.swift`; `M04CaptureEngine.swift`; `PackScanShareSheet.swift`; `PairingProtocol.swift`; `SessionFoundation.swift`; `TrackingFoundation.swift`; `TransferProtocol.swift`; `TransferService.swift`; `TransferTLS.swift`; and `apps/ios-capture/PackLabCaptureTests/PackLabCaptureTests.swift`. Upstream `origin/main` governance commits were synchronized separately; this task did not edit `TASKS.md`.

## Validation evidence

Expected material result: app build succeeds; XCTest executes at least one test and all tests pass; missing results or any failure returns nonzero.

- `git diff --check` — PASS for implementation commits.
- `gh api repos/Sekiph82/PackLab --jq '{private,default_branch}'` — actual result `{"private":true,"default_branch":"main"}`.
- `gh run view 38751526109 --repo Sekiph82/PackLab --log-failed` — failed because the built app plist lacked `CFBundleExecutable`; fixed in `7755652182f738ef31bb9a85bb24bd5de2f148e0`.
- Hosted run `38753546428` at `7755652182f738ef31bb9a85bb24bd5de2f148e0`: unsigned simulator build PASS; 205 XCTest cases executed, 170 passed and 35 failed; summary guard correctly failed. It exposed the missing app executable metadata.
- Hosted run `38755083949` at `c9c0a1c66138c7cbd07bd889cf956fad415c96dd`: runner setup, iOS 18.0 runtime, dependency resolution and unsigned simulator app build all PASS; XCTest executed 205 tests, 173 passed, 32 failed; summary guard correctly failed with `result=Failed`, `failedTests=32`. Actual run: https://github.com/Sekiph82/PackLab/actions/runs/38755083949
- The Debug `-Onone` adjustment reduced but did not resolve existing behavior failures. The suite remains red; this is not independent-audit readiness.
- No local substitutes were used for the hosted macOS build or XCTest run.

## Failure and boundary review

The remaining failures are in existing product/test behavior, including invalid deletion/finalization error expectations, camera focus behavior, capture/pose and session recovery, coverage/detail/base-pass decisions, preflight, share eligibility, and transfer wire-version decoding. They do not indicate a CI build or signing failure. Fixing those behaviors would expand this frozen CI task into unrelated feature work, so the failures remain visible for independent review/follow-up. The CI's nonzero failure behavior is intentional and must remain.

No Windows Installer, OCCT, or OCP rebuild was run. No private sample scans, supplier files, signing material, credentials, or owner data were added to CI or committed. The workflow uses no secrets and uploads no artifacts. GitHub repository privacy was verified as private. Owner Desktop checkout contents were not edited. No disk cleanup was performed. `TASKS.md` was not modified. PL-0355 and M17 were not started.

## Post-task PackLab worktree cleanup

The initial log was published before cleanup. A separate log-only follow-up records the verified result:

- Task-created worktrees: 1 (`codex/pl-0354-macos-ci`).
- Verified safe and removable: 1. It was clean, had no untracked or ignored files, contained no reparse points, had no active process/agent use, and its complete HEAD was an ancestor of `origin/main`.
- Removed: 1 using normal `git -C <stable PackLab checkout> worktree remove <exact task path>` without force. The exact directory is absent and the task worktree is absent from `git worktree list --porcelain`.
- Blocked removals among task-created worktrees: none.
- Older/unrelated worktrees were preserved. Three available historical PL0350/PL0352/PL0353 worktrees have unpublished branch commits and 19,522–20,903 ignored local environment/cache records; three stale R07/ownerdev entries have no corresponding directory. None was created for this task, and none was removed.
- C: free space before removal: `97,186,861,056` bytes. After removal: `97,222,111,232` bytes. Actual net increase: `35,250,176` bytes (about 33.6 MiB).
- Private `origin/main` contained implementation and the initial separate log commit before removal; the log-only cleanup follow-up is also being published to `main`.
- Owner Desktop originals were not edited or removed. No disk/cache cleanup was performed.

## Handoff

Hosted verification is **not green**; do not emit `READY_FOR_INDEPENDENT_AUDIT`. The task's required hosted build and real XCTest were attempted and the failure evidence is recorded above. Independent audit can inspect the implementation and evidence while keeping the test failure explicit.
