# CLAUDE_PEER_REVIEW — PL-0430 AR preview prototype (V02)

Reviewer: Claude Code, an independent peer-review subagent. I did not write this change and made no source, test, doc or TASKS.md edits. All mutations ran on in-memory or temporary copies only.
Scope: commit `151e3da5` (HEAD), which responds to `CLAUDE_PEER_REVIEW_PL0430_V01.md`.
Verdict: **PASS** at prototype tier (eligible for CLAUDE_PEER_AUDITED_PASS).
- On-device AR rendering, tracking, placement and shared-session coexistence are still pending physical iPhone 16 evidence.
- There are no P0, P1 or P2 findings. The P3 findings below do not block acceptance.

## Evidence I gathered myself
- **Local pytest:** `pytest tests/core/test_ar_preview.py` gave 12 passed (Windows .venv, QT_QPA_PLATFORM=offscreen).
- **Lint and types:** `ruff check core apps tools tests` passed with all checks clean. `mypy core apps tools` reported no issues in 290 source files.
- **Windows Python Quality (run 43047092144, sha 151e3da5):** success, with 2922 passed and 18 skipped.
- **macOS Capture (run 43047092315, sha 151e3da5):** success.
  - The `Unsigned iOS device archive` job compiled `ARPreview.swift` for arm64, including the RealityKit branch that sets `ARView.session`. It reported `ARCHIVE SUCCEEDED` with no errors.
  - The simulator XCTest job ran all 3 `ARPreviewPackageTests` cases, and they passed. 209 tests ran with 0 failures, `** TEST SUCCEEDED **`, and the summary guard records `expected=209`, `totalTestCount: 209`.
- **Signing Material Guard (run 43047092419):** success.

## P2-1 and P2-2: closed
Method: a pytest plugin re-executes the mutated `ar_preview.py` source into the module before collection. This is needed because pytest `pythonpath = ["core/src"]` overrides PYTHONPATH, and package data paths resolve relative to the repo. An identity control mutant survived as expected.

| Mutant | Result | Killing test |
|---|---|---|
| M1: mould guard removed | KILLED | `test_authority_and_unit_guards[changes0]` |
| M2: size guard removed | KILLED | `test_size_and_extent_guards` |
| M3: mirror (x,z,+y) | KILLED | `test_frame_conversion_is_a_rotation_and_keeps_outward_winding` |
| M9: reversed winding | KILLED | same test |
| physical-status check removed | KILLED | guards[changes1] |
| authority-class check removed | KILLED | guards[changes2] |
| unit check removed | KILLED | guards[changes3] |
| extent bound removed, or raised to 1000 m | KILLED | `test_size_and_extent_guards` |
| `parent_authority_revision_id` dropped | KILLED | `test_package_names_the_parent_authority_revision` |
| relative units emptied | KILLED | relative-geometry test |
| contract check removed (`ar_preview.py:46`) | SURVIVED | (P3-4) |
| vertex upper bound disabled (`ar_preview.py:59`) | SURVIVED | (P3-4) |

The signed-volume test is not tautological. The source volume is computed independently from the `CadPreviewMeshRevision` vertices in mm, the test asserts that it is > 0, and the packaged volume must match it to within 1e-3 relative. Both a mirror and a winding reversal flip the sign.

## P2-3: resolved by design; the device behaviour cannot be verified here
I judged this from RealityKit/ARKit semantics and the code at `ARPreview.swift:155-181` and `ARTrackingService.swift:88-150`.

**Delegate.** I do not expect assigning `view.session = SharedARSessionOwner.shared.session` to replace the delegate of the session.
- The RealityKit `ARView` reads frames for its camera background and anchoring through internal observation, not the public `ARSessionDelegate`.
- Apple sample code for RealityKit routinely sets `arView.session.delegate = self` on other objects while the view keeps rendering. That would not work if ARView depended on the delegate slot.
- So the `session.delegate = self` assignment in the owner init (`ARTrackingService.swift:97`) should keep receiving pose, tracking and interruption callbacks.

**Configure/run.** With `automaticallyConfigureSession: false`, ARView does not run or reconfigure the session. The default session of the view is never run before it is replaced. No second `ARSession.run` remains, so the shared configuration and `planeDetection` are untouched.

**owner.start() is safe and idempotent.**
- It is guarded by `isStarted` (`ARTrackingService.swift:101-107`), and XCTest at `PackLabCaptureTests.swift:1628` asserts that 2 starts produce 1 run.
- The app already starts the owner at launch (`ContentView.swift:804`, via `runtime.start()` and `trackingService.start()`), and nothing in the app calls `runtime.stop()`. In practice this call is therefore a no-op.
- On a device without ARKit support it only sets `policy.limited(.cameraUnavailable)`, which is the same as the existing behaviour.
- It does not add reset epochs or diagnostics.

**Camera-relative world placement without plane detection.** This is acceptable for a visual reference: the anchor is world-locked and gravity-aligned through `AnchorEntity(world:)`. A shared-session reset (trackingDegraded or interruption) may make the model jump, which is visual only and has no authority impact. The offset maths has a direction issue; see P3-1.

**Dismissal.** There is no `dismantleUIView`. This is correct: the view must not pause the app-wide session.
- Whether the deinit or window removal of a RealityKit ARView leaves a session it does not own untouched cannot be verified without a device. I do not expect it to pause the session.
- If it did pause it, the owner would keep `isStarted == true` and later `start()` calls would be no-ops. Tracking would then stall until an interruption or reset.

**What remains unverifiable without a device:**
- the delegate staying intact while the preview is shown (the pose buffer keeps advancing);
- no new reset diagnostics after opening the preview mid-scan;
- tracking continuing after the sheet is dismissed;
- rendering and placement.

These should be explicit items in the physical iPhone 16 evidence checklist. At prototype tier, behind the default-off `PackLabARPreviewEnabled` flag (`ContentView.swift:781`), I consider that acceptable.

## Swift P3 checks: verified
- `ARPreview.swift:53` requires the physical status `DEFERRED_OWNER_VALIDATION`.
- Line 58 limits `display_scale_basis` to the 2 values the writer emits.
- Line 59 requires the exact `frame`.
- Lines 140-141 check the file size before `Data(contentsOf:)`. The check fails closed when the size is unknown (falls back to Int.max), and `parse` still re-checks `data.count`.
- The golden literal (`PackLabCaptureTests.swift:3183`) contains the DEFERRED status, an allowed basis and the exact frame. It still parses, and CI confirms this (209/209).
- Python also adds `parent_authority_revision_id`. The golden literal omits it and Swift does not require it, so the two stay compatible.
- The criteria and docstring now name physical iPhone 16 evidence instead of PL-0429, and record the licensing and PL-0233 pre-read.

## Findings
### P3 (non-blocking)
1. **The camera-relative offset points sideways in portrait** (`ARPreview.swift:169-175`).
   - The local axes of `ARCamera.transform` refer to the landscape-right sensor orientation: x runs along the long axis of the device.
   - In portrait (`Info.plist:27-32` lists portrait first), camera-local -y is therefore horizontal. The model lands about 0.25 m to the side at 0.6 m, not "below".
   - With aspect-fill cropping in portrait, that is likely at or outside the visible edge. Camera roll and pitch also tilt the offset.
   - Suggested fix: use the camera translation plus the horizontal projection of its -z column times 0.6, and subtract 0.25 on world y. Fix this before the physical evidence run.
2. **Stale wording about plane detection.**
   - The `ARPreview.swift:12-13` header still says the mesh is placed "on a detected horizontal plane".
   - So does criterion 3 in `PL-0430_VALIDATION_CRITERIA_V01.md:5`.
   - Both now contradict the camera-relative world anchor.
3. **The new Swift guards have no XCTest.** The frame check, basis allow-list, DEFERRED status and file-size pre-check have no negative-case test; removing any of them would go unnoticed. The V01 P3-8 gaps also remain: scan_master_replaced, on_device_scale_verified, class/contract and the upper size and coordinate bounds. The pattern is cheap to add: resealed golden variants in `testPL0430AuthorityUpgradeAndBadGeometryFailClosedEvenWithAValidDigest`.
4. **Two Python mutants survive.** The contract check (`ar_preview.py:46`) and the vertex/triangle upper bounds (`ar_preview.py:59-60`) have no test. Each needs one case using the existing `_forged` helper.

## Remaining limits
- On-device rendering, placement, tracking, scale, coexistence with an active scan and dismissal behaviour are not verified; physical iPhone 16 evidence is required.
- Delivery of the package to the phone is manual.
- The digest detects corruption, not tampering by a sender (unchanged from V01).
