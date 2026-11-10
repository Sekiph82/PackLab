# M17 Execution Plan V01

## Scope and order

M17 covers validation data, failure/recovery behavior and V1 acceptance. Implement every software-verifiable task in dependency order, then run one comprehensive M17 validation and one consolidated independent source/security review. Keep device, physical, hosted and business acceptance separate.

## Implementation batches

1. **Golden data and metrics — PL-0369–PL-0374.** Create licensed real reference samples and deterministic synthetic package families outside Git; add measurement/camera/provenance metadata, simulated expected ranges, and a benchmark comparison harness. No Kenya factory or private Kenya scans exist. Software dataset evidence does not claim Kenya physical evidence.
2. **Failure and recovery — PL-0375–PL-0384.** Exercise low-texture, gloss/transparency, capture gaps, corrupt imports, interrupted reconstruction, low disk, restart/recovery, missing/wrong engine versions, and schema migration through focused software fixtures. Preserve failure results and user-data boundaries.
3. **V1 acceptance and limits — PL-0385–PL-0395.** Implement/document every software-verifiable workflow; record physical iPhone/package measurements, native hosted artifacts, and human/security/legal decisions as separate gates when their required device/account/physical evidence is not available. Freeze truthful V1 limitations.

## Dependencies and acceptance boundaries

- PL-0369–0374 share the M17 dataset contract; synthetic geometry, dimensions, materials, tolerances and virtual-camera values are generated assumptions, never measured facts.
- The YCB object-model archives and photographs are independent captures, not calibrated photo/model pairs. No photo camera intrinsics or physical measurements are inferred when the source does not provide them.
- PL-0375–0384 can proceed with software fixtures even when physical/device acceptance is unavailable.
- PL-0385–0394 require real iPhone/iOS/Windows/macOS runners, three scanned package families, physical scale or publishing evidence where each task says so. Keep each incomplete until its own required evidence exists; continue independent software tasks.
- PL-0395 documents limitations and no-direct-mold-manufacture boundary; it cannot convert missing physical evidence into acceptance.

## Relevant source areas

- `core/src/packlab_core/` reconstruction, segmentation, calibration, measurements, import/export and schema services.
- `apps/ios-capture/` iPhone camera/motion capture, PackScan authoring and transfer.
- `apps/windows-studio/` import, reconstruction workflow, Scan Master and Design Model UI.
- `tests/core/`, `tests/studio/`, `tests/ios-capture/`, and `tests/ci/` existing test conventions.
- `tools/datasets/` M17 source extraction, synthetic generation and manifest validation.
- `docs/datasets/` source provenance, license and data-authority boundaries.

## Validation checkpoint

Do not run complete suites after individual tasks. Run the applicable unit/integration/regression, migration, iOS/macOS XCTest, Python format/lint/typecheck, Windows Studio, security/dependency checks and required E2E validations once after feasible M17 implementation is complete. Use focused failure reproductions only when a concrete defect or high-risk acceptance requirement warrants them. Run hosted Actions at the milestone checkpoint only where required and safe; inspect triggers and available billing/account controls first. Do not publish while the local checkout remains divergent/dirty in a way that could expose unrelated owner changes.

## Current external gates

- No real Kenya dataset, Kenya factory or physical package samples are available. Do not ask the owner for scans or folders. Keep physical Kenya validation open.
- This Windows host cannot execute hosted macOS/iOS workflows or the owner’s physical iPhone evidence locally.
- The checkout has owner-local changes and is 95 commits behind `origin/main`; do not reset, merge or publish over that state. Reassess safe synchronization only after the local source/evidence is independently separable and canonical changes can be preserved.

