# CLAUDE_PEER_REVIEW — PR #4 fix/ios-row-buttons — V01

- Reviewer: independent Claude Code peer reviewer (did not implement this PR). These are my own findings, separate from the builder's reports.
- Base `origin/main` 085d510a5232d53bf8d02edcb7f693160828e59b; head `origin/fix/ios-row-buttons` ad69e4dd5e8ad29abfd6b6a68e87682896a28623.
- Files reviewed: `apps/ios-capture/PackLabCapture/ContentView.swift`, `apps/ios-capture/PackLabCapture/Services/SessionFoundation.swift`, `tests/packscan/test_ios_row_button_styles.py`. I also checked every other Swift file under `apps/ios-capture` for List/Form rows.

## Verdict: FAIL (CHANGES_REQUIRED). The fix is a one-line change; see P1-1.

The New Scan fix is correct. But a row in the same file with the same bug, which deletes data, is still unfixed, and the new guard test cannot detect it.

## Root cause
The explanation matches both SwiftUI behaviour and the code. In `NewScanWizard` (head SessionFoundation.swift:753-759), Cancel and Start were default-style buttons in a single Form row. A tap on that row fires both buttons:
- `showProtocol = true` presents the Capture protocol sheet.
- `dismiss()` closes the wizard sheet, which also closes the child sheet, and resets `showNewScan` in the parent.

That is exactly what the owner saw: the protocol sheet flashes, both sheets close, and `onStart` never runs, so no session is created and History stays empty.

I ruled out the other candidates:
- `CaptureProtocolView` (M04CaptureEngine.swift:1302-1307) calls `onContinue` only from an explicit Continue tap, and Continue sits in its own row.
- The two failure paths in `onContinue` (transparent prep not acknowledged; `preflight.canStart == false`) set `validationMessage` and `return` without calling `dismiss()`.
- The success path calls `dismiss()` and the parent also sets `showNewScan = false`. Both target the same sheet, so this is harmless, and it only happens after `onStart`.

The nested `.sheet` on the wizard plus the parent's `showNewScan` cannot dismiss anything by themselves. Device confirmation is still owner-side.

## Findings

### P1-1 — SessionResumeView: Resume also triggers Discard, which deletes the session (unfixed, same bug)
`SessionFoundation.swift:837-844` (head) has a `List(candidates)` row whose `VStack` contains `Button("Resume")` and `Button("Discard")`, both default style. One tap fires both. `ContentView.swift:872-874` `onDiscard` runs `SafeSessionDeleter().deleteDetailed(plan:, confirmed: true)` at the same time as `onResume` reinstalls the session. So tapping Resume can delete the session being resumed from disk, without a confirmation prompt. This bug existed before the PR, but the PR says it fixes "multi-button rows" and this row is in the same file.
Fix: add `.buttonStyle(.borderless)` to both buttons.

### P2-1 — The guard test only catches HStack rows, so it misses P1-1
`tests/packscan/test_ios_row_button_styles.py:17` only matches `HStack \{`, and line 28 only reads `SessionFoundation.swift`. It counts only `Button("` and does not check whether the HStack is inside a List/Form. Because of this it passes on head even though SessionResumeView's VStack row is still broken. It also would not catch `Button {` / `Button(action:)` / `Button(role:` forms, or a list row in another Swift file.
Suggested change: scan the bodies of `List(`/`Form {` in every `*.swift` under `PackLabCapture`, include VStack/HStack/direct children, and match `Button(` and `Button {`.
What it does catch: I ran it in a scratch copy:
- It passes on head (2 passed).
- It fails on base (2 failed).
- It fails when `.borderless` is removed from "Send to PackLab" alone (1 failed).

So it is not tautological for the HStack rows it covers.

### P3-1 — The scan-start error banner cannot be dismissed
`ContentView.swift:740-743`: `scanStartError` is cleared only after the next successful start. It has no tap-to-dismiss or timeout. This is acceptable, but the banner stays on screen indefinitely if the owner never starts another scan.

### P3-2 — `.buttonStyle(.borderless)` changes how the buttons look
Borderless buttons are tinted with no row highlight, and tapping blank space in the row now does nothing. This is the intended behaviour. The owner should confirm the History row and the New Scan Cancel/Start row still look correct on the iPhone 16.

## Other rows (all Swift files under apps/ios-capture)
Every List/Form in the app is covered below; there are no others.
- NewScanWizard Cancel/Start: fixed.
- AcceptedFrameGalleryView Retake/Delete (SessionFoundation.swift:794-811): fixed.
- LocalScanHistoryView Share/Send (SessionFoundation.swift:862-880): fixed. Finalize is alone in its branch; borderless there is harmless.
- SessionResumeView Resume/Discard: **NOT fixed (P1-1)**.
- PairingReceiverView (PairingProtocol.swift:151-168): each button is a direct child of the Section, so each has its own row. OK.
- CaptureProtocolView Continue: single button in its own row. OK.
- NewScanWizard "Review Capture Protocol": single button in its own row. OK.

## Swift 6 / MainActor
`scanStartError` is set inside an unstructured `Task {}` created in a closure in `ContentView.body`. That closure is non-`@Sendable` and inherits MainActor isolation, so the Task runs on the MainActor. The code already called MainActor `runtime.configureM04QualityRuntime(...)` in the same place without `await`, so the new assignments add no new isolation risk. CI agrees: "Unsigned iOS device archive" PASSED (SWIFT_VERSION 6.0, SWIFT_STRICT_CONCURRENCY=complete, SWIFT_TREAT_WARNINGS_AS_ERRORS=YES). There is no compile failure.

## CI (`gh pr checks 4`, at time of review)
- Scan tracked repository for signing material: pass
- Locked Python quality: pass (6m0s)
- Unsigned iOS device archive: pass (1m49s)
- Unsigned iOS Simulator build and XCTest: pass (12m36s, run 44686628935, job 136122384186)

Local: `ruff format --check` and `ruff check` were clean on the new test, run against a scratch copy outside the repo config.

## Required to reach PASS
1. Add `.buttonStyle(.borderless)` to the SessionResumeView Resume and Discard buttons.
2. Widen the guard test so it fails on SessionResumeView without that fix: cover VStack rows inside List/Form and all Swift files.
3. Simulator XCTest: green (done).
4. Owner retest on the iPhone 16: New Scan → Start → Continue creates a session; Resume does not delete it.
