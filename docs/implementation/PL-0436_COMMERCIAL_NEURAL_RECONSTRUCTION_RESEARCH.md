# PL-0436 Implementation Spec — Commercial Neural Reconstruction Research Backend

Status: future M19 research, not a V1 dependency.

## Objective

Prototype a neural reconstruction backend behind the accepted PL-0163 ReconstructionBackend contract without changing downstream project semantics.

## Licensing gate

The original `facebook/VGGT-1B` checkpoint must not be used for commercial PackLab work.

The official VGGT project states that only the separately released `VGGT-1B-Commercial` checkpoint is licensed for commercial usage under the current VGGT license.

Sources:
https://github.com/facebookresearch/vggt/blob/main/README.md
https://github.com/facebookresearch/vggt/blob/main/LICENSE.txt

Before installation:
- owner/license acceptance recorded;
- checkpoint identity/hash recorded;
- redistribution/deployment path reviewed;
- military/application restrictions and acceptable-use terms recorded;
- runtime dependency licenses reviewed.

## Scope

Implement `NeuralReconstructionBackend` only behind the PackLab contract.

Normalized outputs must include:
- cameras/intrinsics;
- point/depth geometry;
- confidence;
- relative/metric-unverified scale state;
- runtime/model provenance;
- optional COLMAP-compatible export if used.

No direct downstream dependency on VGGT classes is permitted.

## PackScan use

Benchmark:
- high-resolution still subsets;
- known capture ordering;
- optional camera priors;
- object/background masks;
- guided orbit versus turntable datasets separately.

Do not flatten PackScan into video unless the experiment explicitly measures that degradation.

## Authority

Until PL-0437 benchmark acceptance, neural reconstruction remains an experimental reconstruction observation and cannot become the default production backend.

## Tests

- adapter satisfies PL-0163 fake/backend contract;
- missing GPU/model fails clearly;
- license/checkpoint configuration must be explicit;
- output cannot claim METRIC_VERIFIED;
- source files remain immutable;
- model-specific paths stay outside portable user provenance.
