# CLAUDE PEER REVIEW — f0d04897 test corrections (V01)

- Reviewer: independent Claude reviewer (did not author f0d04897, 4862ec95, 0176a67e or the Codex tests)
- Date: 2026-11-10
- Repo state reviewed: `main` at e95879ea (f0d04897 is an ancestor; no drift since f0d04897 in any touched test or exercised production file)
- Verdict: **LEGITIMATE (both changes)**. No production defect hidden. No remaining weakening from the c7ffa5db episode.

## Scope

Commit `f0d04897 test: correct two Codex stash assertions that never ran in CI` (4 insertions, 3 deletions):

1. `tests/core/test_packaging_sku_library.py:142-143` (PL-0392 test `test_povu_sku_variants_reuse_one_immutable_package_geometry_revision`): `item.as_dict()["geometry_copied"]` / `["source_mutated"]` changed to `item.as_dict()["geometry_reference"]["geometry_copied"]` / `[...]["source_mutated"]`.
2. `tests/core/test_blender_label_render_overlay.py:174-175` (PL-0391 test `test_dieline_artwork_and_product_mockup_binding_share_authority`): `exported.source_dieline_revision_id == source_dieline.revision_id` replaced by `== print_intent.revision_id` plus a new hop assertion `print_intent.source_dieline_revision_id == source_dieline.revision_id`.

Also checked: c7ffa5db (weakened PL-0379 quarantine test), its revert in d1f3e952 and the production fix in 0176a67e.

## Evidence examined

- `git show f0d04897`, `git log -p` for both test files: both assertions were introduced by 4862ec95 (Codex stash pop), reformatted only by 0176a67e, corrected by f0d04897.
- Production history: `packaging_sku_library.py` has nested `geometry_reference{packaging_asset_id, revision_id, geometry_copied, source_mutated}` since its creation commit 371df092 (only other change 51185827, unrelated). `label_dieline_svg.py` unchanged since c929af19 (PL-0317); `export_label_dieline_svg` sets `source_dieline_revision_id=dieline.revision_id` (`core/src/packlab_core/label_dieline_svg.py:174,181`) and SVG attrs carry both `data-current-dieline` and `data-source-dieline` (`:135-136`).
- Contracts: PL-0317 (AUDITED_PASS) test `tests/core/test_label_dieline_svg.py:38` asserts `export.source_dieline_revision_id == dieline.revision_id` where `dieline` is the print-intent revision, and `:41` asserts `data-source-dieline == dieline.source_dieline_revision_id` (base). PL-0314 print intent pins the base via `source_dieline_revision_id=dieline.revision_id` (`label_metric_surface_binding.py:460`). PL-0391 criterion 1 asks for the export to be bound to "source revision" — no requirement that the export skip the print-intent hop. PL-0392 Codex log V02 describes the flags only as "false", never as top-level keys; the same test's own lines 149-155 assert the nested key set. Docs (`PL-0416_ARTWORK_ONLY_CHANGE_PROCESS.md`) mention `geometry_copied: false` without location.
- Hosted CI run 42854695278 (29dd985a): `2 failed, 2588 passed` — exactly these two tests (`KeyError: 'geometry_copied'`; `'label-dieline-print-intent:431c…' != 'label-dieline:c770…'`). Later quality runs on main containing f0d04897 (42885936327 @727bedbf, 42882742666 @08ed55e2, 42881593961 @28c185e4) concluded success.

## Commands and results (`.venv/Scripts/python.exe`, `QT_QPA_PLATFORM=offscreen`; OCP importable locally)

| Command | Result |
|---|---|
| `pytest tests/core/test_packaging_sku_library.py tests/core/test_blender_label_render_overlay.py tests/core/test_label_dieline_svg.py tests/core/test_label_dieline_print_intent.py` | 31 passed |
| `pytest tests/core/test_label*.py tests/core/test_packaging*.py tests/core/test_blender*.py tests/transfer/test_ingest_controller.py` | 220 passed, 5 skipped (real-Blender smoke gated by `PACKLAB_REAL_BLENDER_SMOKE`) |
| Temp copy (`git archive f0d04897`, scratchpad), pre-fix test files from `f0d04897~1` | 2 failed, 8 passed — exactly the CI failures (KeyError; print-intent vs base id) |

Mutation checks (temp copy only, production source mutated, corrected tests run):

| Mutation | Result |
|---|---|
| M1 `geometry_copied: True` in SKU `as_dict` | corrected PL-0392 test FAILS (plus the older two-SKU test) |
| M2 `source_mutated: True` | corrected PL-0392 test FAILS (only test catching it) |
| M3b production "fixed" to the Codex expectation (export id -> base dieline, identity kept consistent) | corrected test FAILS and **PL-0317 audited test `test_label_dieline_svg.py:38` FAILS**; original Codex test passes |
| M4 print intent pins a bogus base id | caught by production identity check (`label_dieline_print_intent_identity_invalid`) before reaching the test; 8 dieline tests fail |

## Per-change verdicts

### 1. SKU `geometry_reference` nesting — LEGITIMATE
`tests/core/test_packaging_sku_library.py:142-143`. Production has emitted the nested shape since 371df092; the same test already asserted the nested key set (`:151-155`); no doc/criterion specifies top-level flags. The Codex assertion raised `KeyError` (never a value comparison), so it was an authoring error, not an observed defect. The corrected assertion is strictly stronger than the remaining string check (`:146-147`): it pins value and location per related SKU, and is the only test that detects M2.

### 2. Dieline export chain — LEGITIMATE
`tests/core/test_blender_label_render_overlay.py:174-175`. The export pinning the exact dieline revision it rendered (the print intent, which carries safe/bleed boundaries) is the PL-0317 contract, independently audited and tested at `test_label_dieline_svg.py:38`; the base id remains reachable via the print intent and the SVG `data-source-dieline` attribute. Changing production to satisfy the Codex expectation (M3b) breaks that audited test and would drop the pointer to the actually-rendered print-intent revision — a provenance regression. The correction asserts both hops (export -> print intent -> base), so end-to-end coverage of the chain is equal or stronger than the original single (incorrect) hop.

### c7ffa5db context — no residual weakening
c7ffa5db removed the 1100-deep valid JSON case and the oversized-version case from `tests/transfer/test_ingest_controller.py`. d1f3e952 reverted it explicitly; 0176a67e then fixed production (`packscan/container.py:105-124`, `MAX_JSON_NESTING_DEPTH`) and restored/extended the test (deep array, 65-deep object, dotted oversized version -> `unsupported_future_version`, undotted -> `unsupported_version`). Current file contains the full-strength cases and passes.

## Findings

- **P0/P1/P2:** none.
- **P3-1 (naming):** `LabelDielineSvgExport.source_dieline_revision_id` means "the dieline revision exported" (print intent), while on `LabelDielineRevision` the same field name means "base dieline". The identical name with different semantics is exactly what misled the Codex test. Not a defect (PL-0317 contract, audited); consider a doc comment or a future additive `base_dieline_revision_id` field. No action required for f0d04897.
- **P3-2 (coverage, PL-0391 open):** the PL-0391 test does not itself assert the export's Design Model/BREP/zone/placement SVG attributes (criterion 1); this is covered by `test_label_dieline_svg.py:31-50`. PL-0391 also remains blocked on rendered-mockup evidence (criterion 3), per its Codex log.
- **P3-3 (evidence hygiene):** `PL-0392_CODEX_LOG_V02.md:26` describes the test as verifying the flags although it was never run and would have errored; f0d04897 supersedes this. Keep PL-0392 acceptance tied to the post-f0d04897 runs, not the Codex log.

## Limits
Reviewer did not edit source/tests/TASKS.md, commit or push. Real-Blender smoke tests were skipped (env gate). Mutations ran only in a scratchpad copy built by `git archive f0d04897`.
