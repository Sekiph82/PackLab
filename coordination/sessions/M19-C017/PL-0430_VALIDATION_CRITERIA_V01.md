# PL-0430 — Validation Criteria V01 (Claude, written before review)

1. Windows/core produces a bounded, deterministic, digest-bound AR preview package from an existing tessellated Design Model preview (`CadPreviewMeshRevision`), converting units to metres for display only. The package carries visual-reference-only authority: no mould use, Scan Master unchanged, on-device scale not verified.
2. The iPhone app validates the package fail-closed (size, contract, digest, authority, geometry bounds and indices) before showing anything. An altered or authority-upgraded package is rejected.
3. On a device the mesh is placed on a detected horizontal plane via RealityKit, with a visible "AR VISUAL REFERENCE ONLY" banner. Simulators show a non-AR fallback.
4. A feature flag (`PackLabARPreviewEnabled`, default off) gates the entry point; the existing capture workflow is unchanged when it is off.
5. Python tests and simulator XCTests pass in hosted CI (Windows Python Quality, macOS Capture), and a cross-language golden test proves the digest canonicalisation matches. Physical iPhone AR rendering, tracking accuracy and transfer of the package to the phone are not claimed; the iPhone target gate (PL-0429) applies.
