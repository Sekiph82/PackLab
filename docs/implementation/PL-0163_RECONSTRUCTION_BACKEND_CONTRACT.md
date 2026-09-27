# PL-0163 Implementation Spec — Reconstruction Backend Contract

Mandatory pre-read:
https://github.com/Sekiph82/PackLab/blob/main/docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md

## Objective

Create one PackLab-owned reconstruction contract so downstream code never depends directly on COLMAP/OpenMVS CLI syntax and can later host an experimental neural backend without changing project semantics.

## Required domain types

Implement or equivalent-test:

- `ReconstructionBackendId`
- `ReconstructionCapability`
- `ReconstructionInputSet`
- `CameraPrior`
- `ReconstructionJobSpec`
- `ReconstructionStageResult`
- `ReconstructionOutputManifest`
- `CameraSolution`
- `ScaleState`

`ScaleState` must distinguish at minimum:
- `RELATIVE`
- `METRIC_UNVERIFIED`
- `METRIC_VERIFIED`

M07 must never produce `METRIC_VERIFIED`; M09 owns that transition.

## Backend protocol

A backend must expose PackLab semantics equivalent to:

```python
class ReconstructionBackend(Protocol):
    def probe(self) -> CapabilityReport: ...
    def prepare(self, job: ReconstructionJobSpec) -> PreparedJob: ...
    def execute(self, prepared: PreparedJob, cancel: CancelToken) -> ReconstructionRun: ...
    def collect(self, run: ReconstructionRun) -> ReconstructionOutputManifest: ...
    def provenance(self) -> BackendProvenance: ...
```

No UI widget may own these states.

## V1 composition

The COLMAP/OpenMVS lane can be represented as a composite backend:

```text
ColmapOpenMVSBackend
  feature extraction
  matching
  sparse mapping
  COLMAP export
  OpenMVS conversion
  dense cloud
  mesh
  refine
  texture
```

Each stage must produce a machine-readable result and retain stdout/stderr through PL-0164/PL-0179.

## Input handling

Use immutable PackScan source evidence. Working images are copies/derived files created through the project workspace authority.

Camera priors may include:
- source image dimensions;
- focal/intrinsics;
- ARKit pose observations;
- capture ordering;
- orbit/ring metadata.

Every prior records how it is used:
- ignored;
- initialization only;
- fixed;
- refined;
- rejected.

## Output manifest

The normalized manifest must identify:

- backend ID and backend component versions;
- executable/model hashes where practical;
- configuration/preset digest;
- source input digest;
- camera convention;
- cameras and registration status;
- sparse/dense/mesh/texture paths through project-relative asset IDs;
- point/triangle counts;
- scale state;
- known limitations;
- stage results;
- parent project/reconstruction revision.

Do not place private absolute filesystem paths into portable user-facing provenance.

## Future neural backend

Do not implement a neural model in PL-0163. Implement only the contract that would permit one.

A future `NeuralReconstructionBackend` must return the same normalized output and may not bypass M08/M09/M10 authority.

Research spec:
https://github.com/Sekiph82/PackLab/blob/main/docs/implementation/PL-0436_COMMERCIAL_NEURAL_RECONSTRUCTION_RESEARCH.md

## Tests

Mandatory:
- fake backend can complete through normalized job API;
- backend failure maps to deterministic stage failure;
- cancellation cannot mutate RAW_CAPTURE;
- invalid/missing camera prior degrades explicitly;
- two different backend implementations can satisfy the same contract in tests;
- M07 output cannot claim METRIC_VERIFIED;
- manifest contains no private absolute paths;
- changing source revision invalidates a prior reconstruction output.
