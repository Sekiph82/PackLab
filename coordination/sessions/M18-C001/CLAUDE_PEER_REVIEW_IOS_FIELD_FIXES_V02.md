# CLAUDE_PEER_REVIEW V02: iOS field fixes follow-up (PR #9, commit 0e46a356)

- Reviewer: Claude independent peer reviewer. I did not write this code and did not edit any source.
- Scope: `git show 0e46a356`, the follow-up to the findings in V01 (`CLAUDE_PEER_REVIEW_IOS_FIELD_FIXES_V01.md`). Five files changed, +51/-19.
- CI for 0e46a356 (all confirmed with `gh run view`):

| Run | ID | Result |
|---|---|---|
| PackLab Capture macOS CI | 44803079506 | success |
| Unsigned iOS Simulator build and XCTest (job 136519935777) | | **Executed 233 tests, 0 failures**; matches the expected count of 233 |
| Unsigned iOS device archive | | success |
| Windows Python Quality | 44803079266 | success |
| Signing Material Guard | 44803079510 | success |

## Verdict: PASS_WITH_NOTES

## Status of the V01 findings
- **M1: RESOLVED.**
  - The health, `scanStartError` and camera-recovery messages moved out of the top ScrollView. They are now the first items of the bottom VStack (`ContentView.swift:1164-1186`).
  - The layout test (`PackLabCaptureTests.swift:3524-3528`) requires the `healthMessage` frame. It checks that the frame is fully inside `bottomControls` and does not intersect the crosshair zone. The test fails if the warning is not laid out, so it is no longer tautological.
- **M2: RESOLVED.**
  - `Info.plist` now allows only `UIInterfaceOrientationPortrait`.
  - The bottom band gets `.clipped()` (`ContentView.swift:1297`) together with `alignment: .bottom`.
- **M3: RESOLVED (deletion). The protection part is cosmetic.**
  - `SafeSessionDeleter` removes `<sessionID>.packscan` from the pickup directory and reports any failure (`SessionFoundation.swift:747-750`).
  - The test checks that only this session's copy is deleted and that `other.packscan` survives.
- **LOW 5: RESOLVED.**
  - The toast counts required-ring wedges only, measured against `missingSectors` (`ContentView.swift:572-581`).
  - The optional ring chip is dimmed and labelled "optional" for accessibility (`M04CaptureEngine.swift:1704-1706`).
- **NSLocalNetworkUsageDescription: present** (`Info.plist:27-28`). The receiver is reached by literal IP from the QR code, with no Bonjour browsing, so `NSBonjourServices` is not needed.

## New findings (all LOW)
1. **The health warning is the first thing clipped when the bottom band overflows.** `.clipped()` with `.bottom` alignment cuts overflow at the top of the band, and the health warning is pinned there (`ContentView.swift:1167` and `:1297`). This can happen when the turntable keyboard shrinks the band. It is rare and temporary, and the coverage ScrollView should shrink first. The layout test only covers the "center unset" state.
2. **The file protection attribute does not add protection.** `FileProtectionType.completeUntilFirstUserAuthentication` (`SessionFoundation.swift:1109`) is already the iOS default class, so this call adds nothing. The real remedy for M3 is the deletion. Using `.complete` would block USB pickup while the device is locked, so keeping the default is acceptable, but the commit message overstates it.
3. **The deleter only finds pickup copies under the default name.** It looks for `<sessionID>.packscan`, but `ProductionScanFinalizeAction` names the copy after `packageURL.lastPathComponent`. If a caller passes a custom `destination`, the copy is not deleted. Production uses the default name.
4. **The XCTest count stayed at 233.** The existing tests were extended rather than new ones added. This is expected and is not a coverage regression.

## NOT_VERIFIED
- Behavior on a physical iPhone 16, including the Local Network permission prompt and an upload completing end to end to Studio.
- Keyboard overflow on the device.
