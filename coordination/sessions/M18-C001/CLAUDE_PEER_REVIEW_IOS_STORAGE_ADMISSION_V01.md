# CLAUDE_PEER_REVIEW - PR #5 iOS storage admission (V01)

Reviewer: independent Claude source-code reviewer (did not author the change).
Scope: `git diff main...fix/ios-storage-admission` (head e7316966), 2 files, +10/-3.
Evidence inspected: source diff, ContentView.swift call sites, SessionFoundation.swift (ScanSessionStore, SessionDiscoveryService, history index), M04CaptureEngine.swift preflight, test file, CI test-count guard. No device or CI run was executed by this reviewer.

## Verdict: PASS_WITH_NOTES

## Root cause - confirmed
- Old `newScanReadiness` (ContentView.swift ~700): if `PackLabSessions` missing, it checked `isWritableFile` on the parent `Library/Application Support`. iOS does not pre-create Application Support in a fresh app container, and `isWritableFile` on a nonexistent path returns false, so `storageAvailable == false` -> `ScanSuitabilityPreflight` emits `storage_unavailable` blocker (M04CaptureEngine.swift:1155, "Storage admission is unavailable"). Matches device symptom.
- Actual writes never needed the dir pre-existing: `ScanSessionStore.create` (SessionFoundation.swift:95-98) uses `createDirectory(withIntermediateDirectories: true)`; `M04SessionContextStore.persist` likewise. So the gate was the only thing failing.

## Regression check
- Nothing depends on the root's absence. `SessionDiscoveryService.discover` (SessionFoundation.swift:456) and history listing (:631) both `try? contentsOfDirectory` and return `[]` for missing OR empty dir; an empty `PackLabSessions` yields no resume prompt and empty history - identical behavior.
- `ScanSessionStore.create` duplicate guard checks `layout.sessionRoot` (root/sessionID), not the root itself; unaffected.
- Path is identical to `ContentView.sessionRoot` (ContentView.swift:911).
- No change to PackScan/Scan Master/Design Model authority, metrics, or provenance.

## Notes (non-blocking)
1. N1 (low) Side effect in computed property: `newScanReadiness` is evaluated inside the `.sheet` content builder (ContentView.swift:870), i.e. on SwiftUI body evaluation while the sheet is presented, and in tests. `createDirectory(withIntermediateDirectories: true)` is idempotent and cheap (one stat when present), errors are swallowed and the result still falls back to `isWritableFile`, so a real failure still correctly reports unavailable. Acceptable; a one-time `prepareStorage()` in `.task` would be cleaner but is not required.
2. N2 (low) Test is not a strict fresh-install regression test: the added `XCTAssertTrue(vm.newScanReadiness.storageAvailable)` (PackLabCaptureTests.swift:3372) passes regardless of whether Application Support existed beforehand, so it only catches the original bug on a pristine simulator container. It is valid (simulator test host container is writable) and non-tautological against an unwritable-storage regression. Deleting the real Application Support dir in-test would be unsafe, so this is acceptable; true fresh-install proof remains the iPhone 16 retest.
3. N3 (info) Session root path is now duplicated inline vs `ContentView.sessionRoot`; a shared constant would avoid drift. Not required.

## Test-count guard
- `func test` count: main 217, head 217. Change adds an assertion to existing `testPL0118RuntimeReadinessTransitionsFeedExactPreflightEligibility`, no new method. CI guard `.github/workflows/packlab-capture-macos.yml:579 expected=217` unaffected.

## Open / NOT_VERIFIED
- macOS CI result for head e7316966 and physical iPhone 16 fresh-install retest not observed by this reviewer.
