---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 01
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: 7fa07928
alsoReviewed: [b6bf5d67, 8d410b1a, d1f3e952 (TASKS.md state only)]
tasks: [PL-0369, PL-0370, PL-0371, PL-0372, PL-0373, PL-0374]
reviewDate: 2026-11-10
---

# Claude Independent Peer Review V01 — PL-0369..PL-0374

Reviewer did not write the reviewed code. Read-only review; no source, tracker or Git changes made.
The earlier files `CLAUDE_PEER_REVIEW_PL0369_V01.md` and `CLAUDE_PEER_REVIEW_PL0370-0374_BATCH_V01.md`
(non-independent, SUPERSEDED in d1f3e952) were not relied on.

Scope: `git show 7fa07928` (new `tools/datasets/run_benchmark_regression.py`, 4 tests, catalog notes,
implementation log); PL-0369 commits `b6bf5d67` + `8d410b1a` (`core/src/packlab_core/benchmark_metrics.py`,
`tools/datasets/{generate_packaging_benchmark,validate_packaging_dataset,validate_ycb_manifest,extract_ycb_subset,ycb_source_identity,dataset_root}.py`,
`docs/datasets/M17_DATASET_CATALOG.md`, `tests/ci/test_packaging_dataset_manifest.py`); the regenerated local dataset outside Git;
and hosted GitHub Actions results for those commits.

## Commands run (actual output)

1. `QT_QPA_PLATFORM=offscreen .venv/Scripts/python.exe -m pytest tests/ci/test_packaging_dataset_manifest.py -q -p no:cacheprovider`
   ```
   ...........sss.......                                                    [100%]
   18 passed, 3 skipped in 23.16s
   ```
   (3 skips: Windows symlink-privilege fixtures for YCB path tests.)

2. `.venv/Scripts/python.exe tools/datasets/validate_packaging_dataset.py "$LOCALAPPDATA/PackLab/datasets/M17/synthetic/manifest.json"` (exit 0, 11.7 s)
   ```
   {"dataset_id": "packlab-m17-synthetic-packaging-v2", "families": [bottle, closure, jar, jerrycan, pump, sachet, trigger_spray, tube],
    "manifest_sha256": "3a37b55d8b93affdba73d23a39ba299c12053f433000a5911ac7f6e71ea3601b",
    "materials": [hdpe_matte, pet_clear, pet_gloss, pp_translucent], "sample_count": 96}
   ```
   Matches the implementation log and catalog. Local footprint `du -sh synthetic` = 43M. `M17/` contains only `synthetic/`; no `ycb/` directory exists.

3. `.venv/Scripts/python.exe tools/datasets/run_benchmark_regression.py <manifest> --builtin-segmentation --report report.json` (3 m 08 s)
   ```
   {"counts": {"FAIL": 0, "NOT_EVALUATED": 576, "PASS": 192}, "outcome": "PASS"}
   exit=0
   ```
   768 rows; evaluated metrics only `segmentation_iou`/`segmentation_dice`; min observed 0.99993 (matches log).

   Negative runs with `--observed` (no built-in):
   ```
   oob   {"syn_bottle_hdpe_matte_v01": {"reconstruction_extent_x_mm": 9999.0, "segmentation_iou": 0.95}}
         -> {"counts": {"FAIL": 1, "NOT_EVALUATED": 766, "PASS": 1}, "outcome": "FAIL"}  exit=1
   bool  {"syn_bottle_hdpe_matte_v01": {"segmentation_iou": true}}
         -> ValueError: observed metric must be a finite real number: segmentation_iou   exit=1
   empty {} -> {"counts": {"FAIL": 0, "NOT_EVALUATED": 768, "PASS": 0}, "outcome": "FAIL"}  exit=1
   ```

4. Ruff
   - `ruff check tools/datasets/run_benchmark_regression.py tests/ci/test_packaging_dataset_manifest.py` -> `All checks passed!`
   - `ruff check core/src/packlab_core/benchmark_metrics.py tools/datasets tests/ci/test_packaging_dataset_manifest.py --output-format concise` (HEAD) ->
     ```
     core\src\packlab_core\benchmark_metrics.py:13:1: UP035 Import from `collections.abc` instead: `Mapping`
     tools\datasets\generate_packaging_benchmark.py:29:1: E402 / I001; :30:1: E402
     tools\datasets\generate_packaging_benchmark.py:135:9: F841 `body`; :151:5: F841 `obj`
     tools\datasets\validate_packaging_dataset.py:3:1: I001
     Found 7 errors.
     ```

5. Mypy (repo `[tool.mypy]` config, which CI runs as `mypy core apps tools`)
   - `mypy core/src/packlab_core/benchmark_metrics.py tools/datasets/validate_packaging_dataset.py tools/datasets/validate_ycb_manifest.py tools/datasets/run_benchmark_regression.py` -> `Found 13 errors in 4 files`, including
     `benchmark_metrics.py:88,90,94` (object passed to isfinite/compare), `validate_packaging_dataset.py:259,261,263` (Optional arithmetic),
     `validate_ycb_manifest.py:19` (no-redef x3), `:88` (Optional assignment), and
     `run_benchmark_regression.py:126: Argument 2 to "mask_quality_metrics" has incompatible type "MaskRaster | None"`.
   - `mypy tools/datasets/run_benchmark_regression.py` alone -> `Success: no issues found` (packlab_core types not followed in single-file mode). The log's "mypy on the harness: no issues" is literally true only for that invocation, not under CI's invocation.

6. Hosted Actions (`gh run list --commit ...`)
   ```
   8d410b1a  PackLab Windows Python Quality  failure    run 42846623453   (Ruff lint: "Found 12 errors", M17 files listed; mypy errors as above)
   8d410b1a  PackLab Signing Material Guard  success
   7fa07928  PackLab Windows Python Quality  cancelled  run 42850756303
   7fa07928  PackLab Signing Material Guard  success
   d1f3e952  PackLab Windows Python Quality  pending    run 42851951145   (queued at review time)
   ```
   No green hosted quality run exists for any M17 commit; pytest never ran in CI because the job stops at ruff. Local reproduction (4, 5) shows the M17 lint/type errors are still present at HEAD, so the pending run is expected to fail as well.

7. Commit content: `git show --name-only 7fa07928` lists only 4 text files. `b6bf5d67` adds only Python, Markdown and `pyproject.toml`; `8d410b1a` adds only the test file. No PNG/PLY/manifest/`syn_*` assets in `git ls-files`. Grep of the 7fa07928 diff for password/secret/api key/token/supplier/private-key/signing patterns: no hits. Kenya mentions are disclaimers or the negative test id `real_kenya_bottle`.

8. Independent PNG decoder check (scratch script, own encoder): 40 random images over color types 0/2/4/6, sizes 1–23 x 1–17, random per-row filters 0–4, decoded by `read_mask_png` and compared to the expected coverage-channel threshold -> `roundtrip ok 40`. 16-bit, interlaced, palette -> `ValueError: unsupported mask PNG format`. Corrupted CRC -> accepted. Truncated file -> `struct.error`.

## Fail-closed analysis of `run_benchmark_regression.py`

- Production path always validates: `run_regression` calls `validate_manifest(manifest_path)` unconditionally (L135); `main` has no bypass. The two monkeypatches (test file L337, L359) are test-local; the in-band test (L322) and the CLI runs above use real validation.
- Zero evaluated metrics -> FAIL (L165–166; verified with `{}`).
- Non-synthetic authority rejected twice: by `validate_manifest` (manifest flags, per-sample `synthetic is True`, exact `measurement_authority`, band provenance/authority) and by `compare_synthetic_packaging_sample` (benchmark_metrics.py L157–180).
- Unknown samples (L140–142), unbanded metrics (L150–152), bool/NaN/inf/string values (benchmark_metrics.py L88–89) all raise.
- Band integrity: validator recomputes every band from PLY-measured extent and tolerance and rejects drift (validate_packaging_dataset.py L186–206).
- PNG decoder is correct for the supported formats (filters, alpha offset `channels-1` for color 4/6, Paeth tie-breaking) and rejects non-8-bit/interlaced/palette.

## Findings

| ID | Sev | Location | Finding |
|---|---|---|---|
| F0 | **P1** | `tools/datasets/generate_packaging_benchmark.py:29,30,135,151`; `tools/datasets/validate_packaging_dataset.py:3,259-263`; `core/src/packlab_core/benchmark_metrics.py:13,88-94`; `tools/datasets/validate_ycb_manifest.py:19,88`; `tools/datasets/run_benchmark_regression.py:126` | The repo's mandatory hosted quality gate (`windows-python-quality.yml`: ruff L105/mypy L135/pytest L139) fails on M17 code: hosted run 42846623453 failed at ruff; locally 7 ruff + 13 mypy errors remain at HEAD in these files. Because the job stops early, the M17 tests have never run in CI. DoD requires "mandatory hosted/system checks where applicable"; for a "golden dataset **for CI**" this is applicable. Fixes are mechanical (import order/`collections.abc`, unused vars, Optional narrowing, `assert child.raster is not None`, no-redef). |
| F1 | Resolved | `TASKS.md` | At 7fa07928 PL-0370..0374 were `[x]` on the non-independent batch review and the file had committed stash-conflict markers. Verified at d1f3e952: 0 conflict markers; PL-0369..0374 are `[ ]` `IMPLEMENTED_REVIEW_PENDING`, PL-0370 explicitly kept open for real Kenya data. No action needed beyond applying the verdicts below. |
| F3 | P2 | `run_benchmark_regression.py:166` | Aggregate `outcome` is `PASS` (exit 0) while 576/768 metrics (75%) are `NOT_EVALUATED`. Per-metric rows and counts are honest, but a CI gate reading only the exit code would report PASS for a run that never touched reconstruction/fitting. Recommend a `PARTIAL` outcome or `--require-complete` before using the exit code as a gate. |
| F4 | P2 | `run_benchmark_regression.py:85-127` | Built-in "engine" post-processes the ground-truth mask and scores it against that same truth: a valid regression signal for `post_process_mask`, not an independent segmentation engine and nothing about SAM 2.1. Log/catalog say so; do not cite the 192 PASS as segmentation accuracy. |
| F5 | P2 | `validate_packaging_dataset.py:251-319` | Validator enforces camera/intrinsics/pose but not `lighting`, `render` or `material_appearance` beyond `finish`. They are present in the regenerated manifest (verified: 3 area lights with energy/size/position; Eevee, AgX, Blender 5.2.2 LTS; roughness/transmission/warning), but deleting them would not fail validation. |
| F13 | P2 | `tests/ci/test_packaging_dataset_manifest.py:39-75`; repo tree | PL-0369 "golden dataset for CI": nothing dataset-like is committed. CI's fixture is built in the test: 96 copies of one blank white 640x480 RGB, one rectangular mask, one 3-vertex PLY. It is a good schema/integrity/provenance-boundary fixture, but not a golden reference of packaging content. The realistic 96-sample set is local-only, needs Blender, and per the owner notice is *not* externally redistributable. Acceptable minimal reading of V04 criterion 1, but it should be described as "CI contract fixture", not a golden content dataset. |
| F14 | P2 | `tools/datasets/ycb_source_identity.py`; local `M17/` | PL-0369 V04 criterion 3 (downloaded public objects matched against official URL/bytes/SHA-256 and archive content inspected) cannot be verified: no YCB archives or extracts exist on this machine; `test_ycb_source_archive_identity_is_pinned_to_reviewed_bytes` only asserts constants. The "public" half of the dataset is tooling-only. Mark criterion 3 unverified/pending or obtain the two ~10.7 MB Google-16k archives (owner permission for download). |
| F6 | P3 | `run_benchmark_regression.py:36-54` | `read_mask_png`: no CRC check, no IHDR dimension cap, unbounded `zlib.decompress`, `struct.error` on truncation. Only reached after `validate_manifest` bounds the file (hash, 640x480, bounded decompress), so risk is limited to standalone reuse on untrusted input. |
| F7 | P3 | `run_benchmark_regression.py:135-136, 99` | Validate-then-reread TOCTOU (no re-hash). Low risk locally. |
| F8 | P3 | `run_benchmark_regression.py:146-148` | Observer output silently overwrites `--observed` values for the same metric; should raise on conflict. |
| F9 | P3 | `run_benchmark_regression.py:112-118` | Hard-coded provenance `"python", "3.12"` and fixed `created_at`. Cosmetic. |
| F10 | P3 | `tests/ci/test_packaging_dataset_manifest.py:322-378` | No negative test proves `run_regression` rejects a tampered manifest via the real validator. |
| F11 | P3 | `docs/datasets/M17_DATASET_CATALOG.md:33,43` | "deterministic generator ... manifest hash pins the result": Eevee GPU output is not guaranteed bit-identical across GPUs/drivers/builds. Say "deterministic inputs; output hash pinned for this Blender 5.2.2 build". |
| F12 | P3 | `benchmark_metrics.py:135-145` | Reconstruction and parametric-fit bands are identical (mesh extent ± max tolerance); no fit-specific metrics (radius/wall/neck residuals). Acceptable synthetic scaffolding. |
| F15 | P3 | `CLAUDE_IMPLEMENTATION_LOG_PL0369_V01.md` "Inputs verified" | States the test file was "already tracked/committed from prior session"; it was actually missing and added in 8d410b1a. |

No P0 findings.

## Overstatement check

- Physical accuracy, Kenya data, SAM 2.1 accuracy: not claimed anywhere reviewed. Bands are `mm_simulated`, `SYNTHETIC_GENERATOR_SCENARIO`, `NONPHYSICAL_SOFTWARE_TEST_ONLY`.
- Overstatements found: implicit "mypy clean" (F0, item 5), determinism (F11), PL-0369 log provenance of test file (F15).

## Per-task verdicts

| Task | Verdict | Basis |
|---|---|---|
| PL-0369 | **CHANGES_REQUIRED** | F0: the CI deliverable fails the repo's hosted quality gate and its tests have never run in CI. F14: public-source (YCB) verification criterion unverified. F13: CI "golden dataset" is a contract fixture only. Synthetic labelling, owner internal-use notice, no-data-in-Git, secrets/privacy all verified OK. |
| PL-0370 | **EXTERNAL_PENDING_REAL_KENYA_DATA** (keep `[ ]`); synthetic portion functionally **passes**, subject to F0 on the generator | Private dataset regenerated outside Git, validated: 96 samples, 8 families x 4 materials x 3 views, SHA `3a37b55d…`, seed 3692026, camera intrinsics/pose, lens distortion, appearance assumptions, metric units (PLY `comment units meters`). No dataset bytes in Git. |
| PL-0371 | **CHANGES_REQUIRED** (F0 only; functionally passes for synthetic GT) | Per-sample nominal dims, tolerance, PLY-verified extents, camera, lens, lighting, render, material stored on the real manifest. F5 is a P2 follow-up. |
| PL-0372 | **CHANGES_REQUIRED** (F0 only; functionally passes for synthetic bands) | `reconstruction_extent_{x,y,z}_mm` bands for all 96 samples, recomputed/drift-checked; harness FAIL path verified. |
| PL-0373 | **CHANGES_REQUIRED** (F0 only; functionally passes for synthetic bands) | `parametric_fit_extent_{x,y,z}_mm` bands present and enforced. F12 noted. |
| PL-0374 | **CHANGES_REQUIRED** (F0 incl. `run_benchmark_regression.py:126` mypy error; F3 strongly recommended) | Harness validates first, compares supplied engine results (`--observed`, built-in adapter) against per-sample ranges, reports PASS/FAIL/NOT_EVALUATED, fails closed on zero-evaluated, unknown samples, unbanded/non-finite/bool values and non-synthetic authority. Recon/fit NOT_EVALUATED in CI does not defeat the contract: engine output plugs in via `--observed`, as demonstrated. |

## Path to CLAUDE_PEER_AUDITED_PASS

1. Fix the ruff/mypy errors listed in F0 (mechanical), push, and obtain a green `PackLab Windows Python Quality` run that actually executes `tests/ci/test_packaging_dataset_manifest.py`. With that evidence, PL-0371..0374 can be accepted without further functional re-review (re-check the diff only).
2. PL-0374: address F3 (non-PASS aggregate when metrics are unevaluated, or an explicit flag) before any CI wiring relies on its exit code.
3. PL-0369: additionally resolve or explicitly scope F14 (YCB archive verification pending) and relabel F13; then re-review.
4. PL-0370: stays `[ ]` until real Kenya data exists.
