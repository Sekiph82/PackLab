# CLAUDE_PEER_REVIEW — PL-0430 AR preview prototype (V01)

Reviewer: Claude Code, an independent peer-review subagent. I did not write this change and made no source, test, doc or TASKS.md edits.
Scope: commit `93a59b54`, with HEAD at `1d3f7459`. The PL-0430 files are unchanged since `93a59b54`.
Verdict: **CHANGES_REQUIRED** (no P0 or P1 findings; the P2 findings are small to fix). The implementation itself is correct. The required changes are missing tests and one on-device risk.

## Evidence I gathered myself
- `pytest tests/core/test_ar_preview.py`: 5 passed (local, Windows .venv).
- `ruff check core apps tools tests`: clean. `mypy core apps tools`: no issues in 290 files.
- Hosted macOS run 43042456552 (`dfa6741a`) succeeded.
  - The unsigned device archive compiled `ARPreview.swift` for arm64 (the RealityKit branch) and reported `ARCHIVE SUCCEEDED`.
  - All three `ARPreviewPackageTests` cases passed, with 209/209 tests executed. The summary guard expected 209.
- Hosted Windows Python Quality:
  - Run 43042456702 (`dfa6741a`) failed only in `test_neural_reconstruction_io::test_image_resolver_rejects_file_changed_during_digest_check`. That failure is unrelated to this change, and 2914 tests passed.
  - Run 43045541856 (`1d3f7459`) succeeded.
- Geometry probe on the real revolve fixture (6682 vertices, 13360 triangles):
  - The (x,y,z)->(x,z,-y) matrix has determinant +1, so it is a proper rotation (-90° about X), not a mirror.
  - Signed volume is +7.78e-6 m³; the source is +7778 mm³ against an analytic value of 7854 mm³.
  - 100% of triangle normals point outward, so the faces RealityKit draws as front faces are kept.
  - Bounds are x/z ±0.00496–0.005 m and y 0..0.1 m, so the mesh is centred and rests on its base.
- The golden tetrahedron in the Swift test has all 4 faces outward-wound.
- Negative paths:
  - `TriangleMeshData` already rejects NaN/Inf vertices, repeated or out-of-range indices and non-integer indices.
  - The builder rejects `mold_use_authorized` True or 0, an empty triangle list, more than 65,535 vertices, and zero-extent relative geometry.
- No new dependency, network call or download. Only system frameworks are used (SwiftUI, UniformTypeIdentifiers, ARKit, RealityKit). Info.plist is unchanged, and the existing `NSCameraUsageDescription` covers ARKit.

## Python mutation testing (temporary copy only)
- 17 mutants were run against `tests/core/test_ar_preview.py`.
- Killed: no rotation, rest-on-top, cm scale, relative 0.2 m, relative x-extent-only, `scan_master_replaced` True, non-canonical digest separators, swapped source IDs.
- Survived:
  - M1: mold-authority guard removed.
  - M2: size-bounds guard removed.
  - M3: mirror (x,z,+y).
  - M9: reversed triangle winding.
  - Also survived but equivalent or low value:
    - M8/M13 (upstream `TriangleMeshData` already checks this).
    - M11 (the fixture is already centred in x).
    - M10 (rounding to 3 decimals).
    - M12 (relative-extent guard).

## Findings
### P2
1. **Missing tests: handedness and winding are not pinned.** `tests/core/test_ar_preview.py:41-55` only checks extents, so a mirrored transform or reversed indices (M3, M9) passes. With RealityKit's one-sided `SimpleMaterial` (`ARPreview.swift:157`), that regression would render the mesh inside-out.
   - Fix: assert that the signed volume is > 0, or that the normals of a known face point outward.
2. **Missing tests: the builder's authority and size guards.** `ar_preview.py:42-49` is untested (M1, M2). Add `dataclasses.replace(preview, mold_use_authorized=True)` and an oversize or empty-mesh case.
3. **Two ARSessions on device.** `ARPreview.swift:148-152` creates a second ARSession through `ARView` while `SharedARSessionOwner.shared` (`ARTrackingService.swift:88-131`, started by `ContentView.swift:804`) may be running.
   - ARKit runs one camera session at a time. The shared owner's `sessionWasInterrupted` immediately re-runs its own session (`reset(reason: .interruption)`). That can make the two sessions fight over the camera and add reset epochs and diagnostics to an in-progress scan.
   - The entry point is available whenever the flag is on, including mid-scan. There is no `dismantleUIView` to pause the session.
   - Fix (any one):
     - Reuse the shared session (`ARView(..., automaticallyConfigureSession: false)` and assign `session`).
     - Pause and restore the shared session.
     - Hide the entry point while a scan is active, and record the remaining risk for the on-device gate.
   - This does not affect the default build, because the flag is off by default.

### P3
4. **Wrong gate reference.** `ar_preview.py:10` and `PL-0430_VALIDATION_CRITERIA_V01.md:7` call PL-0429 the "iPhone target gate". PL-0429 is "remote iPhone capture control from Windows Studio". The criteria also do not mention "commercially licensable" or which mandatory pre-read (PL-0233) was followed.
5. **Unknown units are treated as relative.** `ar_preview.py:52-60` sends any coordinate unit other than `mm_unverified` down the relative path; for example "mm" is accepted and labelled RELATIVE. It should fail closed unless the unit is `reconstruction_units`.
6. **Builder does not check source authority.** `ar_preview.py:42-43,90` checks only `mold_use_authorized`. It copies `physical_accuracy_validation_status` verbatim (a constructed preview with "VALIDATED" is accepted) and does not check `contract` or `authority_class`. `CadPreviewMeshRevision` has no `__post_init__`. Swift does not check this field either (`ARPreview.swift:44-50`).
7. **Writer and reader bounds differ.** The mm path in `ar_preview.py` has no extent bound: 50 m and 1e296 m meshes are emitted, and zero-extent mm meshes are accepted. Swift rejects |coordinate| > 10 m (`ARPreview.swift:61`). Add the same bound in the writer.
8. **Swift parser checks are incomplete.**
   - `ARPreview.swift:54`: `display_scale_basis` is free text shown in the banner. It should be limited to the 2 known values.
   - `frame` is not checked.
   - `ARPreview.swift:135`: `Data(contentsOf:)` reads the whole file before the 8 MiB check.
   - The `scan_master_replaced`, `on_device_scale_verified`, class and contract checks, and the upper size and coordinate bounds, have no XCTest. Each of those mutants would survive. The digest, mold, index-range, degenerate-triangle, flag-default and axis-order mutants are killed.
9. **Traceability.** The package omits `parent_authority_revision_id`, the Scan Master or parent revision that PL-0233 traceability expects. It carries only `parent_kind`.

### Digest review (no finding)
- The splice in `ARPreview.swift:83-99` handles a non-zero `startIndex` correctly.
- On writer output, the first `"content_sha256":"` is always the top-level key. Quotes inside strings are escaped, and the authority object has fixed keys.
- The digest has no key, so anyone can reseal a crafted document; it detects corruption, not tampering by a sender. Duplicate keys and non-canonical whitespace cannot bypass the checks, because authority and geometry are validated on the parsed object after the digest check.
- JSON `0` for `mold_use_authorized` bridges to `false`, which is the safe direction. `1` or `true` is rejected.

## Remaining limits
On-device rendering, tracking, scale and two-session behaviour are not verified; physical iPhone evidence is required. Delivery of the package to the phone is manual.
