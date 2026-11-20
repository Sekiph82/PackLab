# CLAUDE_PEER_REVIEW: iOS field fixes (PR #9)

- Reviewer: Claude independent peer reviewer (did not write this code)
- Scope: `git diff origin/main...origin/fix/ios-crosshair-clear`, head `e33eca4e` (7 commits)
- CI: macOS run 44797874882 (`gh run view`): both jobs green (Simulator XCTest, expected count 233; unsigned device archive). The Swift 6 strict-concurrency and warnings-as-errors risk is settled by that green build.
- Evidence I inspected myself: source diff, the five simulator screenshots in the `ui12` scratch folder, `core/src/packlab_core/packscan/container.py`, `schemas/packscan/manifest.schema.json`, and a Python emulation of the Swift writer (see section 5).

## Verdict: PASS_WITH_NOTES

None of the findings is HIGH. Three MEDIUM findings should be tracked as follow-ups. Physical and iPhone 16 behavior is NOT_VERIFIED by this review, because only the simulator and CI were available.

## Findings

### MEDIUM
1. **Important top messages can be hidden behind the guidance panel.** See `ContentView.swift` around lines 1131-1165 on the branch. The health warning, `scanStartError` and camera recovery (including the "Retry camera" button) are laid out *after* the guidance panel, inside a ScrollView whose height is `crosshairY - 40`. The `main-screen-center-unset` screenshot confirms this: the serious-thermal / low-storage / low-battery warning from `WarningDeviceHealthProvider` is not visible, and nothing shows that the area can be scrolled. The layout test only checks `unsetVM.healthMessage != nil`. It never checks that the message is on screen, so the test passes even though the warning is hidden.
   - Mitigation: hard stops still appear in the bottom area as "Manual blocked: health_hard_stop / camera_not_ready".
   - Fix: put health, error and recovery messages *before* the guidance panel, or pin them outside the ScrollView. Then assert that their frames lie inside `topOverlay`.
2. **In landscape, the bottom controls can grow over the crosshair.** See `ContentView.swift` around line 1285 (`.frame(height: max(0, geo.size.height - crosshairY - clearBand), alignment: .bottom)`). `Info.plist` allows LandscapeLeft and LandscapeRight. In landscape the bottom area is about 140 pt tall. The fixed-height items (blocked-reason plate, buttons, toast, tracking capsule) need roughly 200 pt in the unset screenshot. `.frame(height:)` does not clip, so content aligned to the bottom spills upward over the crosshair. The same can happen when the turntable angle TextField keyboard shrinks the safe area while `windowMidY` (which ignores the safe area) stays where it was. No test covers landscape or the keyboard.
3. **Pickup copies in Documents are never removed.** See `SessionFoundation.swift:1086-1103` and `Info.plist` (`UIFileSharingEnabled` + `LSSupportsOpeningDocumentsInPlace`). Every finalized `.packscan`, including all scan photos, is copied into Documents. These copies are visible in the Files app and over USB/AFC, without explicit file protection. `documentDirectory` appears nowhere else in the app (grep), so deleting a session does not delete its copy, and the scan stays exposed after the user deletes it. The sessions themselves stay in Application Support, so a user can only tamper with the copy, never with the authoritative package; that part is fine. The overwrite is remove-then-copy and silent on failure (`try?`). That is acceptable for a best-effort copy, but a failure is invisible to the operator.

### LOW
4. **The new refusal gates are not tested at the point where they run.** See `ContentView.swift:594-603`. `object_not_in_view` and `camera_below_table` are never exercised through `performManualCapture`. Only `viewAngleToCenter` and `instruction` are unit-tested. I checked the transform layout and it is correct: `ARTrackingService.swift:324` `rowMajor` puts `columns.2.{x,y,z}` at indices 2/6/10 and the translation at 3/7/11. So forward = -Z column and lens y = `[7]` match ARKit, and the gate is not using a transposed matrix.
5. **Optional lower ring: the UI and counts are not fully consistent.** `OrbitGuidanceDial` still shows a "lower" chip without marking it as optional. The toast at `ContentView.swift:574` uses `capturedSectors.count`, which includes optional lower wedges, against `+ missingSectors.count`, which counts required wedges only. So it can show for example "5/18" when 3 of 16 required wedges are done. Completion and `isComplete` are correct.
6. **Snapshots saved before this change are not restored on resume.** Their `configuration` still has lower `required: true`, so `restoreM04OrbitCoverage` (`ContentView.swift:321-324`) rejects them because the configuration no longer matches. An in-progress session resumed after the app update restarts coverage from empty. The photos are kept. I found no Python or Windows consumer that assumes 24 required sectors.
7. **Turntable sessions are declared as `freehand` in the manifest.** See `SessionFoundation.swift:337-341`. Only the `provenance` string records that it was a turntable session. This is documented with a `ponytail:` comment, but downstream code reading `capture_mode` will treat it as freehand.
8. **`minimum_view_count` does not match what completion requires.** Guided-orbit sets `minimum_view_count = bins` (8), while completion now requires 16 wedges.
9. **Finalize now fails without a readable session draft.** It throws `invalidManifest` if `metadata.json` (the `NewScanDraft`) is missing or unreadable (`SessionFoundation.swift:310-312`). Older sessions without a draft can no longer be finalized.
10. **The manifest test does not use the real validator.** `testCanonicalSessionManifestMatchesPackScanManifestSchema` checks a hand-copied version of the schema, so it can drift from the real one. No CI step runs `validate_packscan` on a package produced by Swift.

## 5. ZIP and manifest cross-check (my own emulation)
- The central-directory order is now correct per the ZIP spec: name/extra/comment lengths, disk, internal attributes, external attributes, offset, then the name.
- The checksum for `manifest.json` is computed over the exact canonical bytes stored in the archive (`PackScanWriter.swift:29-48`).
- **How I tested it:** I wrote a Python emulation of the Swift writer. It reproduces the byte layout: raw deflate with `-MAX_WBITS`, the UTF-8 flag, the date 0x21, and JSONSerialization escaping `/` as `\/`. It also builds the manifest as `packScanManifest` does: `kind` `other` for `metadata/accepted-records/*`, an ISO8601 `Z` timestamp, and a device block.
- **Result:** `validate_packscan` **accepts** the emulated packages for both guided_orbit and freehand. It **rejects the old layout** with `corrupt_zip`.
- **Limit:** this is an emulation, not bytes produced by the device. It indicates that a package written by Swift should now validate without manual repair.
