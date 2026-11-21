# CLAUDE_PEER_REVIEW - PR #19 repeatable fit / reproducible build (PL-0462, PL-0463) - V01

Reviewer: independent Claude peer reviewer (not the builder). Date 2026-11-21.
Scope: origin/main...origin/fix/repeatable-fit-build, head 30c5bf97d273b36c5fd67ef319ca1651a4c94820 (5 commits);
apps/windows-studio/src/packlab_studio/measure_design.py and build_model.py; tests/studio/test_measure_design.py and test_build_model.py.
Builder evidence (PR body, PR comment 7055337516) is quoted only where I re-checked it myself.

## What I verified myself
- Focused tests at 30c5bf97 (detached temp worktree, Desktop .venv): test_measure_design.py + test_build_model.py, 28 passed.
- CI run 44850839003 "PackLab Windows Python Quality": completed/success, headSha 30c5bf97, branch fix/repeatable-fit-build.
- Real builds C:\Users\sekip\Documents\PackLab-work\pl0463-repeat\data-20261121-035409 / -040026 / -040633: SHA-256 of
  outputs/colmap/sparse/0/ cameras, images, points3D, frames and rigs .bin is identical across all three (cameras 3bc88322...,
  images 15db9d85..., points3D ae61a706...). database.db bytes differ in all three (9d572b01..., b46f93f4..., 9f902783...),
  so "database contents identical" can only mean the rows, not the file.
  Manifest configuration_digest is ca48b3fd... for the three seeded runs and 216458bf... for the three pre-seed runs, which fits
  DETERMINISM being part of the hashed configuration.
- COLMAP 4.2.1 (OwnerDev engines/colmap/bin/colmap.exe -h): --default_random_seed (default 0), --FeatureExtraction.num_threads,
  --TwoViewGeometry.random_seed (default -1), --Mapper.random_seed (default -1) and --Mapper.num_threads all exist on the
  commands that use them. The flags are correct.
- Gate probe: my script on the PR fixture _ring_scan_master, with the old axis_radial_cv re-implemented from origin/main.
  Scripts: C:\Users\sekip\AppData\Local\Temp\claude\57fb7811153eaca1\6a444d85-9a45-42be-b7f5-fbce40ad634c\scratchpad\probe.py and probe2.py.

| fixture (0.3 mm noise) | old CV | new CV / axis offset | new verdict |
|---|---|---|---|
| oval 40/31, 40 % arc | 0.087 refused | 0.006 / 15.0 mm | FIT D=81.6 |
| oval 40/31, 50 % arc | 0.090 refused | 0.015 / 12.8 mm | FIT D=81.5 |
| oval 40/31, 60 % arc | 0.088 refused | 0.047 / 12.0 mm | FIT D=81.7 |
| oval 40/31, 2/3 arc (PR test) | n/a | above 0.05 | refused |
| dent 4 mm over 60 deg, 2/3 arc | 0.051 refused | 0.037 | FIT |
| full oval 40/30, quarter ring, 1/8 sliver | refused | refused | refused (unchanged) |

## Findings

### HIGH-1 - The free LMedS axis weakens the accepted roundness gate for partial ovals
measure_design.py robust_axis_roundness (about lines 1290-1325 at 30c5bf97) fits an unconstrained circle centre to the side band
and measures CV about it. Nothing limits how far that axis may be from the Scan Master z axis or how far its radius may be from the
measured body radius, and axis_inlier_fraction is not gated.

Any 40-60 % arc of a clearly oval wall (40/31 mm) fits a circle 12-15 mm off the axis with CV below 0.05. The core owner-review
bounds (coverage at least 0.60, section CV at most 0.45) let it through, and the result is a revolve Design Model with D about
81.6 mm for an object that is 62-80 mm. The old axis-centred metric refused all three. This is the "silent gate weakening" that
PL-0462 forbids, and it hits exactly the partial-capture case the task is about.

Fix: isolate_object already bounds its own circle (shift at most 0.15 of the footprint, radius at most 1.2 of the footprint). The
roundness gate needs similar bounds, sized to the measured 2-3 mm bias: for example axis offset at most about 5 mm or 10 % of the
radius, fitted radius within a few % of the measured body radius, and a minimum inlier fraction. Add regression tests at 40-60 %
arcs. The 4 mm dent case (0.051 to 0.037) is marginal, but it is a second sign of weakening and should be reported.

### MEDIUM-1 - Max body diameter semantics changed without a method id, note or test
measure() (about lines 937-953) now skips slices below 10 % of height and reports a 3-slice median instead of the slice maximum.
- Packages whose widest point is in the bottom 10 % (tapered tubs, flared bases) are under-reported.
- A real bead or flange narrower than 3 slices is smoothed away.
- "Neighbours" are list neighbours, so they can be far apart in z when slices were skipped.

None of this is recorded in the Measurements notes or in a versioned measurement method id. ISOLATION_METHOD went to v2, but that
covers the plane and axis changes, not the diameter rule. No test covers the base band or the spike. This changes reported
dimensions (the PR itself cites 80.3 mm before), so it needs a recorded method id or note in the dimension report, plus one test.

### MEDIUM-2 - Coverage thresholds were tuned on the evaluation set; the shown repeatability is only repeatable refusal
The 4-of-5 slices and 2-vertices-per-bin rules were chosen on the same 8 test-333 builds used to show consistency. Any strict
enough threshold gives uniform refusals there. These rules are stricter, which is the safe direction, and they are recorded (method
id ..._min2_..._slices4_v2, and as_dict is hashed into the strategy reason). But:
- the vertex-count rule depends on mesh resolution and object size, and is not tested for small diameters or coarse meshes;
- no real capture shows a repeatable PASS.

The PR body is stale: it still says "at least 3 slices must count". Fix it.

### MEDIUM-3 - PL-0447 real-scan evidence is no longer reproducible
Comment 7055337516 shows the original test-333 build now gets "cannot judge roundness" (2 judged slices).

Recommendation: keep PL-0447 [x], because its acceptance (editable Design Model, authority persistence) is still shown by
synthetic and workflow tests. Add a dated annotation: "EVIDENCE_SUPERSEDED 2026-11-21: the test-333 real-scan fit (H 34.2 / D 76.2)
is refused by the PL-0462 v2 coverage rule; real-scan fit pending a side-covered capture". Cross-reference PL-0462. Do not rewrite
the historical numbers.

### LOW
- L1: --default_random_seed 0 is the COLMAP default already. It is harmless and explicit. Matching threads stay free, and FAISS
  nondeterminism is documented.
- L2: OpenMVS has no seed. The residual nondeterminism (177.5k-181.1k points) is documented in code and in the PR, which fits the
  PL-0463 "document residual" clause. Copy the dimension spread (max body diameter 63.9-71.4 mm across the seeded runs) into the
  TASKS.md evidence.
- L3: The PR should say "sparse model files byte-identical", not "database identical".
- L4: The plane, seed, flag and single-vertex tests are meaningful. The oval test sits only at a 2/3 arc, which is exactly where it
  is refused, so it hides HIGH-1.

## Questions answered
1. Gate: stricter on coverage, weaker on partial ovals (HIGH-1). Quarter ring, sliver, full oval and 6 mm dent are still refused.
   A good 2/3 partial jar fits.
2. 4 slices / 2 vertices: recorded in the method id and provenance, and conservative, but justified only on the tuning set
   (MEDIUM-2).
3. Max body diameter change: not acceptable while unrecorded (MEDIUM-1).
4. COLMAP flags: correct for 4.2.1. The cost (about 25 s more extraction, single-threaded mapper) is acceptable.
5. Provenance: DETERMINISM is in the stage and job configuration, and the configuration digest changes with it. Roundness
   evidence is hashed.
6. PL-0447: see MEDIUM-3.
7. Tests: see L4 and HIGH-1.

## Verdict
CHANGES_REQUIRED (HIGH-1, MEDIUM-1).
- PL-0462 stays open.
- PL-0463: the flags, provenance and sparse identity are verified. It stays open, because its acceptance ("same .packscan gives the
  same model") is not met while OpenMVS is nondeterministic. It could be closed with the limitation recorded if the coordinator
  reads the "where supported" clause that way.

Re-review after the axis bounds and the diameter recording are added.
