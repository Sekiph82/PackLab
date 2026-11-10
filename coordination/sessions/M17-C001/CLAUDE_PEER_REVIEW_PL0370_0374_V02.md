---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 02
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: c62220f2
remediationCommit: 0176a67e
supersedes: CLAUDE_PEER_REVIEW_PL0370_0374_V01.md (verdicts only; V01 evidence still stands)
tasks: [PL-0369, PL-0370, PL-0371, PL-0372, PL-0373, PL-0374]
reviewDate: 2026-11-10
---

# Claude Independent Peer Review V02 — PL-0369..PL-0374 re-review

The reviewer is non-implementing. This is a read-only re-review: no source, tracker or Git changes were made.
Local `main` = `origin/main` = `c62220f2` (after fetch).

## What changed since V01 (7fa07928 -> HEAD)

Only `0176a67e` touches the M17 files. To isolate meaning from formatting, I compared each file with `ast.unparse` before and after:

| File | Semantic change |
|---|---|
| `tools/datasets/run_benchmark_regression.py` | `PARTIAL_PASS` outcome (L186–192); exit 0 PASS / 2 PARTIAL_PASS (0 with `--allow-not-evaluated`) / 1 FAIL (L221–225); explicit `child.raster is None` guard (L135–136). |
| `core/src/packlab_core/benchmark_metrics.py` | `collections.abc.Mapping`; `value = float(raw)` after the same finite/type check. No behaviour change. |
| `tools/datasets/validate_packaging_dataset.py` | `Any` annotations only. |
| `tools/datasets/generate_packaging_benchmark.py` | Type annotations; unused `body`/`obj` bindings removed; tuple construction made explicit with identical values. No output change. |
| `tools/datasets/validate_ycb_manifest.py` | Local variable renamed `record` -> `pinned`. |
| `tools/datasets/extract_ycb_subset.py` | Annotations; an unmatched YCB image name now raises `ValueError` instead of `AttributeError` (stricter fail-closed behaviour). |
| `tests/ci/test_packaging_dataset_manifest.py` | The partial-observation assertion now expects `PARTIAL_PASS` (L433). |
| `docs/datasets/M17_DATASET_CATALOG.md` | Documents the new outcome and exit-code semantics. |

No validation rule was weakened. The generator change does not alter outputs, so the existing local dataset hash is still the reference.

## Commands run at HEAD (actual output)

```
ruff check core apps tools tests                         -> All checks passed!
mypy core apps tools                                     -> Success: no issues found in 285 source files
pytest tests/ci/test_packaging_dataset_manifest.py -q    -> 18 passed, 3 skipped in 28.80s
validate_packaging_dataset.py <manifest>                 -> sample_count 96, manifest_sha256 3a37b55d8b93affdba73d23a39ba299c12053f433000a5911ac7f6e71ea3601b, exit 0
run_benchmark_regression.py <manifest> --observed oob.json        -> FAIL  {FAIL 1, NOT_EVALUATED 766, PASS 1}  exit=1
run_benchmark_regression.py <manifest> --observed empty.json      -> FAIL  {NOT_EVALUATED 768}                  exit=1
run_benchmark_regression.py <manifest> --observed partial.json    -> PARTIAL_PASS {PASS 1, NOT_EVALUATED 767}   exit=2
  ... same --allow-not-evaluated                                  -> PARTIAL_PASS                               exit=0
  ... oob.json --allow-not-evaluated                              -> FAIL                                       exit=1
run_benchmark_regression.py <manifest> --builtin-segmentation     -> PARTIAL_PASS {PASS 192, NOT_EVALUATED 576} exit=2
  ... same --allow-not-evaluated                                  -> PARTIAL_PASS                               exit=0
```
`--allow-not-evaluated` cannot convert a FAIL into exit 0 (verified with the oob case).

Hosted Actions (`gh run list --workflow windows-python-quality.yml`):
- `42854695278` @ `29dd985a`: **failure**. Ruff lint, Ruff format and Mypy were **success**. Tests: `2 failed, 2588 passed, 16 skipped, 1 deselected`. The two failures were `tests/core/test_blender_label_render_overlay.py::test_dieline_artwork_and_product_mockup_binding_share_authority` and `tests/core/test_packaging_sku_library.py::test_povu_sku_variants_reuse_one_immutable_package_geometry_revision`, both unrelated to M17. The M17 tests are not `slow`-marked (the only deselected test is `tests/test_pytest_markers.py:48`), so they ran and passed.
- `42857124635` @ `c62220f2` (HEAD): **success**. `All checks passed!`; `2605 passed, 16 skipped, 1 deselected, 2 warnings in 178.88s`.

## V01 findings status

| ID | V01 sev | Status |
|---|---|---|
| F0 hosted quality gate red | P1 | **Resolved.** Ruff and mypy are clean locally, and hosted run 42857124635 passed with the M17 tests executed. |
| F3 aggregate PASS with NOT_EVALUATED | P2 | **Resolved.** `PARTIAL_PASS`, exit 2 by default; verified above. |
| F1 tracker state | — | Resolved in d1f3e952 (see V01). |
| F4 built-in adapter is post-processing on GT, not SAM 2.1 | P2 | Open as a documentation caveat. Already disclosed and does not block. |
| F5 validator does not enforce `lighting`/`render`/full `material_appearance` | P2 | Open. Data is present in the manifest. Recommended follow-up; does not block PL-0371 "store". |
| F13 CI "golden dataset" is a contract fixture only | P2 | Open. PL-0369 only. |
| F14 YCB archive verification not performed (no archives present) | P2 | Open. PL-0369 only. |
| F6–F12, F15 | P3 | Open nits (PNG decoder bounds outside the validated path, TOCTOU, observer overwrite, hard-coded provenance, no tampered-manifest harness test, determinism wording, identical recon/fit bands, PL-0369 log wording). |
| F16 (new) | P3 | `main()` exit codes 2/0/1 and `--allow-not-evaluated` have no CI test; only `run_regression` outcome strings are tested. Verified manually above. |

No P0/P1 findings remain for PL-0370..0374.

## Per-task verdicts

| Task | Verdict |
|---|---|
| PL-0369 | **IMPLEMENTED_REVIEW_PENDING — owner decision.** The code and CI gates are now green. The task stays open pending the owner's decision on committing redistributable sample files to the public repo (F13), and on YCB archive verification (F14). |
| PL-0370 | **EXTERNAL_PENDING_REAL_KENYA_DATA** (keep `[ ]`). The **synthetic portion passes**: 96-sample private dataset outside Git, manifest SHA `3a37b55d…` revalidated at HEAD, provenance/seed/camera/materials/metric units, no dataset bytes in Git. |
| PL-0371 | **CLAUDE_PEER_AUDITED_PASS** (synthetic ground truth). Real calibrated capture conditions remain external. F5 is a recommended follow-up. |
| PL-0372 | **CLAUDE_PEER_AUDITED_PASS** (synthetic reconstruction bands). A real reconstruction run is external to this task. |
| PL-0373 | **CLAUDE_PEER_AUDITED_PASS** (synthetic parametric-fit bands). F12 noted. |
| PL-0374 | **CLAUDE_PEER_AUDITED_PASS.** The harness validates before comparing. It compares engine results with per-sample ranges, fails closed, and distinguishes PASS / PARTIAL_PASS / FAIL by exit code. Hosted CI is green at HEAD. |

All passes are software/synthetic only: `NONPHYSICAL_SOFTWARE_TEST_ONLY`, with no physical, factory, Kenya or SAM 2.1 accuracy claim.
