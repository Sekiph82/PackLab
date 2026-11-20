# CLAUDE_PEER_REVIEW — PR #4 fix/ios-row-buttons — V02 (supersedes V01)

- Reviewer: independent Claude Code peer reviewer (did not implement this PR). These are my own findings, separate from the builder's or coordinator's reports.
- Base `origin/main` 085d510a; V01 head ad69e4dd; **V02 head f2f12b166f174e7c112deb7ae481ba027f71148a**.
- Re-reviewed the diff from ad69e4dd to f2f12b16: `ContentView.swift`, `Services/SessionFoundation.swift`, `tests/packscan/test_ios_row_button_styles.py`. The branch also adds my V01 review file to `coordination/`; that is coordinator bookkeeping and does not affect the code.

## Verdict: PASS_WITH_NOTES

## V01 findings
- **P1-1 (Resume also runs Discard): RESOLVED.** `SessionFoundation.swift:842-844`: both `Button("Resume")` and `Button("Discard")` now have `.buttonStyle(.borderless)`. Each tap runs only its own action. `.foregroundStyle(.red)` is still applied after the style, which is fine.
- **P2-1 (guard only covered HStack rows): RESOLVED.** The guard now:
  - scans `APP.rglob("*.swift")`;
  - finds the containers `List(...) {` and `Form {`;
  - inside each container, looks at `HStack`/`VStack` rows (with or without arguments);
  - counts buttons with `\bButton\s*(?:\(|\{)`, which covers `Button("`, `Button(action:`, `Button(role:` and `Button {`.
- **P3-1 (error banner could not be dismissed): RESOLVED.** `ContentView.swift:743-744` adds `.onTapGesture { self.scanStartError = nil }` and an accessibility hint. The banner sits in the main overlay VStack. The only `allowsHitTesting(false)` (line 842) is on the pose-debug overlay and does not cover the banner.
- **P3-2 (borderless look): unchanged.** The owner should check it visually on the device.

## Guard discrimination (I ran these myself)
I made scratch copies of every `apps/ios-capture/PackLabCapture/**/*.swift` at each revision and ran the head guard with `python -I -m pytest`:

| Swift sources | Result |
|---|---|
| head f2f12b16 | 2 passed |
| origin/main 085d510a | FAIL: 4 offending rows in SessionFoundation.swift (NewScan, Gallery, Resume, History) |
| V01 head ad69e4dd | FAIL: 1 offending row (Resume) |
| head with `.borderless` removed from Resume only | FAIL: 1 offending row |
| head with `.borderless` removed from NewScan Cancel only | FAIL: 1 offending row |

The guard is not tautological. Its self-test (`test_guard_detects_the_original_device_bugs`) uses inline strings that reproduce the original NewScan and Resume patterns, plus a fixed example that must pass.

## New notes (none blocking)
- **P3-3: offender labels are not useful.** `_block` returns text starting at the `{`, so `row.splitlines()[0]` is just `"{"`. The failure message names the file but not the row; the base run showed `['{', '{', '{', '{']`. Suggestion: take the label from the text just before the brace, e.g. the first `Button(` match in the row.
- **P3-4: the guard is a heuristic with known gaps.** It does not see:
  - multi-button rows built without an H/VStack, such as a `Label` or a custom row view in another struct;
  - `LazyHStack`/`LazyVStack`;
  - a `.buttonStyle(.borderless)` applied to the container. That correct pattern would be flagged as a false positive, which fails safe.

  Today every List/Form in the app is covered: NewScanWizard, Gallery, Resume, History, Pairing and CaptureProtocol (see V01).
- **P3-5: VoiceOver cannot activate the banner.** It is a `Text` with `.onTapGesture`; it has a hint but no `.isButton` trait. A `Button` with plain style would be more accessible. Cosmetic.

## Swift 6 / MainActor
No change from V01. `onTapGesture` mutates `@State` from `body`, which is MainActor-isolated, so this is fine.

## CI (`gh pr checks 4`) for head f2f12b16
All four checks are green on head f2f12b16. Run 44688155247 reports conclusion `success` for headSha f2f12b16.
- Scan tracked repository for signing material: pass (11s, run 44688155259)
- Locked Python quality: pass (6m55s, run 44688155253)
- Unsigned iOS device archive: pass (1m51s, run 44688155247). Compiles under Swift 6, strict concurrency complete, warnings as errors.
- Unsigned iOS Simulator build and XCTest: pass (12m59s, run 44688155247)

## Remaining for full acceptance
Owner retest on the iPhone 16:
- New Scan → Start → Continue creates a session that appears in History.
- Resume restores a session without deleting it.
- Tapping the error banner dismisses it.
