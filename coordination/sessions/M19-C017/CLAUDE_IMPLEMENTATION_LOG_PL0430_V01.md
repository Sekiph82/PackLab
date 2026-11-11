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
