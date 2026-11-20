# CLAUDE_PEER_REVIEW: PR #7 iOS Manual Capture visibility (V01)

- Reviewer: Claude Code independent peer-review subagent (separate from the builder; read-only apart from this file)
- Branch: `fix/ios-capture-button-visible` @ `ae1ef7cdc39ef5fda42920e2677416d8b87f5e83`
- Diff: `git diff main...fix/ios-capture-button-visible`, 2 files, +9/-0
- Verdict: **PASS_WITH_NOTES**

## What I checked myself
- `pytest tests/packscan/test_ios_row_button_styles.py`: 2 passed.
- XCTest `func test` count in `PackLabCaptureTests.swift`: main=217, branch=217. That matches the CI guard `expected=217` in `.github/workflows/packlab-capture-macos.yml:579`.
- Swift structure in `ContentView.swift:787-826`: `ScrollView { VStack(spacing: 4) { ... } }.frame(maxHeight: 320)` is balanced. The two added `}` close the VStack and the ScrollView after the ring/completion VStack's modifiers. `Button("Manual Capture")` (827-831) and the manual warnings/blocked text (832-835) stay outside the ScrollView, inside `if runtime.m04CoverageActive`. Nit: the moved block was not re-indented.
- `catch FinalizationError.invalidManifest` (`SessionFoundation.swift:877`) is a valid enum-case catch pattern. `FinalizationError` is declared at :491, and the generic `catch` comes after it.
- Turntable `TextField`/`Button` inside the ScrollView still work, because ScrollView does not block hit-testing on its children. The decimal-pad keyboard has no dismiss control, but that problem existed before this PR.
- Root cause of the hidden button is plausible. `m04Evaluation` is nil in production (see N1), so the quality block above it is not rendered. The overflow therefore came from the coverage detail alone. With the detail capped at 320 pt, the header, focus line, 320 pt scroll area, button and bottom capsule fit within the iPhone 16 height. The layout can still overflow if healthMessage, scanStartError and cameraRecovery banners all show at the same time. That is low risk, but device confirmation is still needed.

## Findings
### N1 (MAJOR for the user goal, outside this PR's diff): Manual Capture can never accept a photo in production
- `requestManualCapture` (`ContentView.swift:463-466`) guards on `let evaluation = m04Evaluation`. If that is nil, it returns a blocked decision.
- `m04Evaluation` is set only at `ContentView.swift:193` (nil, inside `configureM04QualityRuntime`) and at :400 (`analyzeM04Candidate`). `analyzeM04Candidate` has no production caller: grep over `apps/` finds only the definitions, the internal forwarding call at :414, and tests.
- Result: after this PR the button is visible but every tap shows "Manual blocked: metadata_unavailable / pose_evidence_unavailable" (`evaluateManualCapture`, :435-438). Zero accepted photos means finalize still throws `invalidManifest`. The new history text "Take photos with Manual Capture first" cannot be satisfied yet.
- Recommendation: merge this PR as a layout fix. Open a follow-up to wire a live AR/camera frame into `analyzeM04Candidate`, or to relax the manual path when there is no evaluation. Do not claim the device capture flow is fixed until a real iPhone 16 produces an accepted photo and a finalized `.packscan`.

### N2 (MINOR): the friendly message also covers non-empty-record invalidManifest throws
- On the production path (`ProductionScanFinalizeAction` -> `finalizeCanonicalAcceptedSession`), `canonicalRecords()` at :330 is the empty-records site. The throws at :501 and :506 repeat the same `records.isEmpty` check, so they cannot fire after :330 has passed.
- `SessionFinalizer.validate` at :521/:523 also throws `invalidManifest` for a malformed or duplicate/unsafe payload manifest. In that case "no accepted photos yet" would be wrong. This is rare because the manifest is written by the app itself.
- Optional fix: throw a distinct error (for example `noAcceptedCaptures`) from :330. That would change the enum, so check the tests that match on `invalidManifest`. Alternatively, word the message as "no accepted photos yet (or invalid manifest)".

### N3 (NIT)
- The inner `VStack(spacing: 4)` changes the spacing of the moved rows. Before this PR they used the outer VStack's default spacing. The change is cosmetic.
- `ScrollView` is greedy, so it always takes the full 320 pt even when the content is shorter.

## Not verified
- I did not compile or run the app on a device or simulator. Compile success relies on review and macOS CI.
- No device screenshot after the fix.
