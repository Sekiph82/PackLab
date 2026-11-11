# Claude implementation log — PL-0377 transparent PET (V02)

Date: 2026-11-11. Implementer: Claude Code. This is not a review. It responds to P2-4 in
`CLAUDE_PEER_REVIEW_PL0375_0384_V01.md`: there was no clear-PET fixture, criterion 2 was untested,
and the iOS test could not run on Windows.

- New `tests/core/test_pl0377_transparent_pet.py` (6 tests) on both clear-PET samples of the public
  golden subset (`syn_jar_pet_clear_v02`, `syn_sachet_pet_clear_v01`):
  - **Criterion 1:** the clear-PET render deterministically triggers the object-surface low-texture
    warning, gives `review_required`, and makes the PL-0414 rescan decision route to
    surface-treatment review and never `proceed`.
  - **Criterion 2:** the generated mesh is closed (control: 0 boundary edges). A seeded, labelled
    simulated transparency dropout removes a camera-facing window (98 and 22 boundary edges). The
    PL-0424 anomaly detector then reports `REVIEW_REQUIRED` with `mesh_boundary_edges_present`.
    Physical status stays `DEFERRED_OWNER_VALIDATION`, mould use is not authorized, and scale stays
    `RELATIVE`.
  - **Criterion 3:** the manifest marks the material `pet_clear` with transmission > 0 and the
    "not measured" idealized-shader warning, the sample is synthetic, and the measurement authority
    says no physical truth.
- **iOS / macOS:** the hosted macOS Capture CI runs the full XCTest suite, including the pre-existing
  PL-0113 transparent-preset tests, so the "must run on macOS" gate is met by hosted CI rather than
  being external.
  - That workflow had failed since 4862ec95: all 206 tests passed, but the guard still expected 205.
  - The extra test is `testPackScanWriterRejectsPythonIncompatiblePaths`, from Codex's PackScan
    writer resource/path limits; it mirrors the Python container limits from PL-0379.
  - The guard count is updated to 206.
- No physical optical test, real clear-PET photos, segmentation inference or Kenya evidence is claimed.
