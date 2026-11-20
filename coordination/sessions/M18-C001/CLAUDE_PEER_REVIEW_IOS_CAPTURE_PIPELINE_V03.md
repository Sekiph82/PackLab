# CLAUDE_PEER_REVIEW — iOS capture pipeline V03 (delta)

Reviewer: Claude Code independent reviewer subagent (not builder, not CHATGPT_AUDIT / CODEX_PEER_REVIEW)
PR: Sekiph82/PackLab #7, branch fix/ios-capture-button-visible
Scope: `git diff c875c523..140ace33` (apps/ios-capture/PackLabCapture/ContentView.swift only, +37/-27)
Prior: V02 PASS_WITH_NOTES at c875c523

## Verdict: PASS_WITH_NOTES

## Checks
- Layout only. The change moves existing view blocks around. Gate logic, rules, bindings and runtime calls are the same.
  - CoverageGridView and the ring/base/asymmetric/completion VStack were moved verbatim (same expressions, modifiers and fonts) from the end of the scroll content to the top (ContentView.swift:917-938).
  - Manual warnings now sit inside the 320pt ScrollView (939-944). The new `!manual.warnings.isEmpty` guard only skips building an empty VStack. Warnings render with `.caption2.monospaced()` and white text. Before this commit they inherited the outer style.
  - The quality readout, preset, reflection guidance and turntable block are unchanged and now follow the warnings (945-977).
  - Blocking reasons are still shown under the button (993-999), with the same text and `manualBlockHint` mapping. They are now on a black 0.72 rounded plate, shown only when the list is non-empty.
- Nothing was dropped. Every item shown at c875c523 is still rendered: grid, ring statuses and guidance, detail guidance, base, asymmetric, completion, missing and optional areas, warnings, blocked reasons, quality, preset, reflection and turntable.
- The SwiftUI structure is correct. Braces balance: ScrollView > VStack closes at 978-979, and `.frame(maxHeight: 320)` is still applied to the ScrollView.
- The Manual Capture button is intact. It keeps the `.disabled(!runtime.admitCapture() || runtime.manualCaptureInFlight)` condition, `accessibilityIdentifier("manualCaptureButton")`, and the GeometryReader frame reporter (`onAppear`/`onChange` -> `onManualCaptureFrame`), unchanged at 981-991.
- Screenshot (Simulator, worst case): the grid is at the top of the bounded scroll, Manual Capture is fully visible below it, and the two blocking reasons are readable on the dark plate. "Tracking unavailable" appears at the bottom.

## CI (140ace33), checked via `gh pr checks 7`
- Unsigned iOS Simulator build and XCTest: pass (run 44750361473). The 222 executed / 0 failures count comes from the coordinator; this reviewer did not re-inspect the logs.
- Unsigned iOS device archive: pass (run 44750361473).
- Signing-material scan: pass.
- Locked Python quality (run 44750361306): attempt 2 still in_progress when this review was written, so NOT_VERIFIED green. The failing test, tests/studio/test_shutdown.py::test_bounded_timeout_and_non_cancellable_job, is a Python Qt timing test. The PR diff vs origin/main touches only .github/workflows/packlab-capture-macos.yml and apps/ios-capture/** Swift, with no Python or studio files. That check looks at Python only (it cannot see the Swift changes), so the failure is unrelated to this PR. Merge should still wait for the rerun to pass.

## Notes (non-blocking)
1. In the Simulator screenshot, the "Camera unavailable in Simulator" placeholder text shows through and overlaps the bottom of the grid and the button area. The placeholder is Simulator-only and was not introduced by this delta. It is cosmetic.
2. Moving the warnings into the scroll area means they can now scroll out of view when the grid is tall. This is acceptable because warnings do not block capture, and blocking reasons stay pinned under the button.
3. Real iPhone 16 on-device visual confirmation is still pending (owner/device gate). It is not claimed here.
