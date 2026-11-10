---
coordinationSchema: packlab-coordination/v1
artifactType: claude-implementation-log
cycleId: M17-C001
version: 01
actor: CLAUDE_CODE
status: IMPLEMENTED_REVIEW_PENDING
startingCommit: 260beb49
tasks: [PL-0370, PL-0371, PL-0372, PL-0373, PL-0374]
---

# Claude Implementation Log V01 — M17-C001 — PL-0370..PL-0374

## Starting point

Codex M17 logs (`PL-0370_CODEX_LOG_V02.md`, `PL-0371..0374_CODEX_LOG_V01.md`) recorded these as
`LOCAL_COMPLETE_AUTONOMOUS_QUEUE_ARMED` with tests not run. Their source (generator, validator,
`benchmark_metrics.py`, CI tests) was published with PL-0369 (`b6bf5d67`, `8d410b1a`). The
generated local dataset Codex referenced was not present in this execution context.

## Work done

1. **PL-0370** — Regenerated the synthetic benchmark outside Git with Blender 5.2:
   `blender --background --factory-startup --python tools/datasets/generate_packaging_benchmark.py -- --out %LOCALAPPDATA%/PackLab/datasets/M17`
   Result: 96 samples (8 families x hdpe_matte/pet_gloss/pet_clear/pp_translucent x 3 views),
   ~43 MB, manifest SHA-256 `3a37b55d8b93affdba73d23a39ba299c12053f433000a5911ac7f6e71ea3601b`.
   `validate_packaging_dataset.py` on it: PASS (all 8 families, 4 materials, 96 samples).
   Physical path: MSIX-virtualized `...\Packages\Claude_*\LocalCache\Local\PackLab\datasets\M17\synthetic`
   (documented in the catalog). Nothing from the dataset is in Git.
2. **PL-0371** — Per-sample ground truth already in the manifest: nominal simulated dimensions (mm),
   simulated tolerance, mesh-derived extents (validated against the PLY), camera intrinsics/extrinsics,
   lens distortion, lighting rig, render settings, material appearance assumptions. Verified on the
   regenerated manifest by the validator.
3. **PL-0372 / PL-0373** — `expected_software_metric_bands` per sample: reconstruction extent x/y/z and
   parametric-fit extent x/y/z (mm_simulated) plus segmentation IoU/Dice, all with
   `SYNTHETIC_GENERATOR_SCENARIO` provenance and `NONPHYSICAL_SOFTWARE_TEST_ONLY` authority. Validator
   recomputes bands and rejects drift.
4. **PL-0374** — Added `tools/datasets/run_benchmark_regression.py`: validates the manifest (fail-closed),
   takes engine results from `--observed` JSON and/or the built-in segmentation engine adapter
   (PackLab `post_process_mask` + `mask_quality_metrics` on each GT mask, alpha-channel coverage matching
   the validator), compares via `compare_synthetic_packaging_sample`, reports PASS/FAIL/NOT_EVALUATED
   per metric. Unevaluated metrics never count as PASS; zero evaluated → FAIL; unknown samples,
   unbanded metrics and non-finite values raise. Exit 0 only on PASS.

## Files changed

- Added `tools/datasets/run_benchmark_regression.py`
- `tests/ci/test_packaging_dataset_manifest.py`: 4 harness tests; ruff import-order fix
- `docs/datasets/M17_DATASET_CATALOG.md`: regeneration record, MSIX location caveat, harness usage

## Test evidence (this session, `.venv` Python 3.12)

- `pytest tests/ci/test_packaging_dataset_manifest.py` → **18 passed, 3 skipped** (symlink privilege) in 53s
- Real dataset: `run_benchmark_regression.py <manifest> --builtin-segmentation` →
  `{"counts": {"FAIL": 0, "NOT_EVALUATED": 576, "PASS": 192}, "outcome": "PASS"}`, exit 0; min IoU/Dice 0.99993
- ruff: clean; mypy on the harness: no issues

## Limits / open items

- **PL-0370 real Kenya subrequirement stays `EXTERNAL_PENDING_REAL_KENYA_DATA`** — no factory or real
  Kenya packaging scans exist. The synthetic proxy is complete; the checkbox should stay open.
- Reconstruction and parametric-fit metrics are `NOT_EVALUATED` in CI: COLMAP/OpenMVS and the fitting
  pipeline are not run here. Their engine outputs plug in via `--observed`.
- Built-in segmentation adapter post-processes ground-truth masks; it exercises the harness and
  post-processing engine, not SAM 2.1 accuracy.
- Material optics are idealized Eevee shaders; no physical accuracy claim.

## Status

`IMPLEMENTED_REVIEW_PENDING` — independent non-implementing Claude review requested.
