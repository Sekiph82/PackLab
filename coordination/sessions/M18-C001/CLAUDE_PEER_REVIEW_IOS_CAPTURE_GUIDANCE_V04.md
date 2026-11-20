# CLAUDE_PEER_REVIEW — iOS capture guidance V04 (delta)

- PR: #8, branch `feat/ios-capture-guidance`
- Range: `e3250015..8bf75027` (prior V03 at e3250015 = PASS_WITH_NOTES)
- Reviewer: independent Claude peer reviewer (not builder/tester; not CHATGPT_AUDIT / CODEX_PEER_REVIEW)
- Date: 2026-11-20

## Verdict: PASS

## Diff inspected
`apps/ios-capture/PackLabCapture/ContentView.swift:1223-1224`: the only change in the range (1 file, +2/-1).
`.buttonStyle(.bordered).tint(.white)` becomes `.buttonStyle(.borderedProminent).tint(.orange)`, with a comment explaining why.
Nothing else changed: the button label, the action (`runtime.setObjectCenterFromScreenCenter()`), the
`accessibilityIdentifier("setObjectCenterButton")` and the surrounding layout are all the same. This is a style-only change.
It does not touch capture gating, the metric/pose path or provenance, and it does not affect PackScan, Scan Master or Design Model authority.

## Evidence (my own runs)
- `python -m pytest tests/packscan/test_ios_row_button_styles.py -q`: 2 passed. The row-button guard is not affected because this button is not in a guarded row.
- `gh pr checks 8`: all 4 checks pass (Locked Python quality, signing-material scan, Unsigned iOS Simulator build + XCTest, Unsigned iOS device archive).
- `gh run view 44771059242`: headSha 8bf75027d0051e946298c230a6279558e2d368db, conclusion success. The log shows "Executed 231 tests, with 0 failures (0 unexpected)".
- Simulator screenshot (`ui7/9BE66A53-...png`): "Reset center" shows as a filled orange button next to the blue "Manual Capture", with clear contrast.

## Notes (non-blocking)
- N1: The orange fill matches the crosshair color, which is what was intended. However, it makes "Reset center" look as prominent as the primary "Manual Capture" button. This is acceptable for UX, and the owner may want to tone it down later.
- N2: The screenshot is from the Simulator. It shows the dark overlay background, not the white A4 mat itself. Visibility over the real white mat on an iPhone 16 is still NOT_VERIFIED (physical device gate). Logically it holds, because a filled orange button with white text does not depend on the background.
- N3 (pre-existing, not part of this delta): in the Simulator the coverage sector grid draws over the "Camera unavailable in Simulator" placeholder text. This is cosmetic and limited to the Simulator.

V03 notes carry forward unchanged.
