# PL-0437 Implementation Spec — Reconstruction Backend A/B Benchmark

Status: future M19 research.

## Objective

Compare the production COLMAP/OpenMVS lane with any license-cleared neural reconstruction backend using the same PackLab capture evidence and physical ground truth.

## Minimum benchmark objects

At least:
- matte bottle;
- glossy/reflective bottle;
- jerrycan or handled asymmetric package.

Use owner-approved/public benchmark evidence only. Do not commit confidential Kenya supplier scans to the public repository.

## Ground truth

Record physical measurements with the approved M09/M17 benchmark procedure.

Minimum comparison dimensions:
- height;
- max width;
- max depth;
- body diameter where applicable;
- neck/finish candidate diameter;
- base diameter/footprint.

## Reconstruction metrics

Record:
- successful/registered input ratio;
- runtime;
- peak host RAM;
- GPU/VRAM where measurable;
- point/triangle counts;
- object surface coverage;
- holes/floating components;
- repeatability across repeated runs/scans;
- dimension error after the same M09 scale procedure;
- failure diagnostics;
- operator intervention.

## Decision rule

Do not select a neural backend because it is faster or prettier.

Any production-default change requires:
- license clearance;
- equal or better PackLab acceptance metrics for the target packaging classes;
- deterministic/reproducible provenance;
- no regression in Scan Master authority;
- explicit ADR.

Until then COLMAP/OpenMVS remains the production baseline.
