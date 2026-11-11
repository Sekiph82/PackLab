# Claude implementation log — PL-0430 AR preview prototype (V01)

Date: 2026-11-11. Implementer: Claude Code. This is not a review.

- **Core:** `core/src/packlab_core/ar_preview.py` → `build_ar_preview_package(CadPreviewMeshRevision)` returns canonical JSON with `content_sha256`.
  - Metric-unverified millimetres are converted to metres; relative geometry is normalised to a labelled 0.1 m display size.
  - The mesh is centred on its footprint, rests on its base, and is converted from source Z-up to RealityKit Y-up.
  - Size is bounded (65,535 vertices / 131,072 triangles).
  - Tests: `tests/core/test_ar_preview.py` (5), including a cross-language golden check against the Swift test literal.
- **iOS:** `apps/ios-capture/PackLabCapture/Services/ARPreview.swift`.
  - `ARPreviewPackage.parse` validates fail-closed. The digest is checked by removing the `content_sha256` member from the canonical bytes and re-hashing with `SourceIntegrity.digest`.
  - `ARPreviewFeatureFlag` defaults to off.
  - `ARPreviewEntryView` opens a `.json` package through the Files picker.
  - `ARPreviewRealityView` (device only) builds a RealityKit `MeshDescriptor` and anchors the mesh to a horizontal plane under an orange "AR VISUAL REFERENCE ONLY" banner.
  - `ContentView` shows an "AR Preview" toolbar button only when the flag is on. Added to the Xcode project.
- **XCTest:** 3 new tests (golden parse, tamper rejection, authority-upgrade and geometry rejection with a valid re-sealed digest). The macOS workflow's expected count is now 209.
- **Not done / limits:**
  - No Studio UI writes the package yet; `build_ar_preview_package` is a library call.
  - Delivery to the phone is manual, via the Files app.
  - Rendering on a real iPhone, AR tracking and scale are unverified; this needs the iPhone 16 target gate.

## V02 fixes after `CLAUDE_PEER_REVIEW_PL0430_V01.md` (CHANGES_REQUIRED)

- **P2-1:** new signed-volume test. The packaged mesh keeps the source mesh's positive volume, so a mirrored axis map or reversed winding fails. Both mutants were verified to fail.
- **P2-2:** new tests for the builder guards: mould authority, physical status, authority class, unsupported unit, too few vertices or triangles, and extent over 10 m.
- **P2-3:**
  - `ARPreviewRealityView` now reuses the app's single `SharedARSessionOwner.shared.session`, using `ARView(cameraMode: .ar, automaticallyConfigureSession: false)`. It no longer runs a second ARSession that could compete for the camera or inject resets into a scan.
  - The model is placed 0.6 m ahead of and 0.25 m below the current camera in world space. Plane detection is no longer needed, and the shared configuration is unchanged.
  - The coexistence of this view with an active scan on device is unverified.
- **P3:**
  - Builder:
    - checks the preview contract, authority class and DEFERRED physical status;
    - rejects units other than `mm_unverified` and `reconstruction_units`;
    - bounds extent to 10 m, matching the phone;
    - records `parent_authority_revision_id`.
  - Swift:
    - checks the `frame`, an allowed `display_scale_basis` and the DEFERRED physical status;
    - checks the file size before reading.
  - Criteria wording: the gate is physical iPhone 16 evidence, not PL-0429; the licensing and PL-0233 pre-read lines were added.
