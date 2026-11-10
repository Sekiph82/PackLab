---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M19-C008 / M19-C009 / M19-C011 / M19-C012 / M19-C013 / M19-C014
version: 01
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: 093551f06696089a910ac00210f04a2ebd9bc7ff
codeIntroducedIn: [260beb49, 0176a67e]
tasks: [PL-0427, PL-0428, PL-0431, PL-0432, PL-0433, PL-0434]
tier: prototype
---

# Independent peer review: M19 scan-station and Studio prototypes (PL-0427, 0428, 0431..0434)

I did not write this code. Codex wrote it, and it was published in `260beb49`, with small mypy and ruff fixes in `0176a67e`. I edited no source, test, doc or tracker file. I did not commit, push, stash, reset or switch branches. All probes and mutants ran from scratch scripts in the session scratchpad. Each mutant ran against a full temporary copy of `core/src`, `apps/windows-studio/src`, `tests/` and `schemas/`, with its own `pytest.ini`. The repository was never modified.

## Scope and inputs read

- For each task I read the TASKS line (839, 840, 846..849), the frozen `*_VALIDATION_CRITERIA_V01.md`, `*_CODEX_PROMPT_V01.md` and `*_CODEX_LOG_V01.md`, the full source module and the full test module.
- Contracts the code depends on: `scan_master.py` (`ScanMasterRevision`, `promote_scan_master` identity body), `design_model.py` (`DesignModelRevision` and its validation, `_revision_id`), `packaging_asset.py` (`FieldProvenance`, `PackagingMeasurement`, `PackagingAsset`, `_bounded_text`), `packaging_sku_library.validate_targets`.
- During the review, HEAD moved from `731262fa` to `093551f0`. `git diff 0176a67e HEAD` over all 12 in-scope files and the three contract modules is empty.
- None of the six modules is imported by any app route, shell or other production module (grep). Each is a library or injectable component that nothing calls.

## Commands and results

| Command | Result |
|---|---|
| `pytest -q` on the 6 in-scope test files (`QT_QPA_PLATFORM=offscreen`, `-B`) | **35 passed** in 5.5 s |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | Success: no issues found in 288 source files |
| `gh run list --branch main --limit 6` | Latest Windows Python Quality on `731262fa` (run 42889760029): **success**. Previous run 42888098053 on `ef5eb681` logged "2696 passed, 16 skipped, 1 deselected", which includes these modules. The run for the current HEAD `093551f0` was not checked. |

Codex log claims checked against reality: the focused test counts in the logs (8 / 4 / 4 / 9 / 4 / 3) match the current files, with 0427 now at 11 after later additions. The no-hardware, no-network and no-path claims hold: the 0427 and 0428 modules import only stdlib, and `PackagingAsset` text fields reject absolute paths and URIs. The log statements that the 0431 preview mesh is caller-supplied, and that no app route is wired, are accurate.

## Mutation discrimination (temp copies)

| ID | Mutation | Result |
|---|---|---|
| m01 | 0427: drop the strictly-increasing ring check | killed |
| m02 | 0427: drop the alternating half-step offset | killed |
| m03 | 0427: pose `angle_status` set to `OBSERVED` | killed |
| m04 | 0427: pose ID no longer includes `recipe_id` | **survived** |
| m05 | 0428: `floor(score*span + 0.5)` → `floor(score*span)` | **survived** |
| m06 | 0428: drop the 0/360 coverage-span check | **survived** |
| m07 | 0428: drop the duplicate `sector_id` check | **survived** |
| m08 | 0428: drop `geometry_sha256` from the plan-id identity | **survived** |
| m09 | 0428: drop `geometry_sha256` validation | **survived** |
| s01 | 0431: drop the manifest `authority_class == SCAN_MASTER` check | **survived** |
| s02 | 0431: drop the manifest `mold_use_authorized is False` check | **survived** |
| s03 | 0431: `is_exactly_scan_fitted` ignores the digest half | **survived** |
| s04 | 0431: metadata authority set to `AUTHORITATIVE` | killed |
| s05 | 0431: drop the ghost guard on the combo-box (user) path | **survived** |
| s06 | 0432: accept UNKNOWN provenance (upstream `PackagingAsset` also enforces) | survived (defense in depth) |
| s07 | 0432: cm→mm ×10 removed | killed |
| s08 | 0432: x-advance ignores diameter | killed |
| s09 | 0432: allow negative gap | **survived** |
| s10 | 0433: provenance forced to `SUPPLIER_FACT` | killed |
| s11 | 0433: drop the duplicate-revision check | killed |
| s12 | 0433: `ranked: True` | killed |
| s13 | 0433: drop the non-`PackagingAsset` rejection | **survived** |
| d01 | 0434: disclaimer not drawn in the PDF | **survived** |
| d02 | 0434: drop the revision-digest check | survived (the check is tautological: both values come from the same `canonical_json`) |
| d03 | 0434: visible `[provenance]` tag removed from the PDF | **survived** |
| d04 | 0434: drop the parse/page-count gate | survived (not reachable with valid input) |

## Findings

No P0 or P1 findings.

### P2 (blocking for the named task)

**P2-1 (PL-0428). Frozen criterion 4 is violated: planned azimuths can duplicate and can fall on the sector boundary.** `core/src/packlab_core/adaptive_angle_plan.py:169-180` computes `start + (i+0.5)*width/count`, then `round(angle, 9)`. Nothing checks sector width, uniqueness or strict containment. Probe: sectors `(0, 1e-12, score 1.0)` and `(1e-12, 360, 0.0)` return planned angles `[0.0, 0.0, 0.0, 0.0, 180.0]`. That is four duplicates, all on the sector's start boundary, which contradicts "lie strictly inside their sector … duplicate azimuths are absent". To fix, either reject sectors narrower than a minimum width (for example 1e-6 deg × max count), or fail closed after allocation when an angle is duplicated or not strictly inside its sector. Add a test for either.

**P2-2 (PL-0428). Criteria 1–3 are not tested in a way that discriminates.** Mutants m05..m09 all survive the 4-test module, so none of these would be caught today:
- removing `geometry_sha256` validation;
- unbinding the plan ID from the geometry digest (criterion 1);
- removing the 0/360 span check or the duplicate sector-ID check (criterion 2);
- changing the score→count rounding (criterion 3: tests use only scores 0.0 and 1.0).

Add tests for:
- invalid or uppercase geometry digests;
- plan-ID change when the digest changes;
- coverage that does not start at 0 or end at 360;
- duplicate sector IDs;
- intermediate scores (probe: 0.16→1, 0.17→2, 0.5→3, 0.83→3, 0.84→4).

**P2-3 (PL-0431). The authority boundary on the Scan Master input is not pinned by tests.** `apps/windows-studio/src/packlab_studio/design_review.py:72-77` rejects a manifest whose `authority_class` is not `SCAN_MASTER` or whose `mold_use_authorized` is not `False`. My probe confirms the code is correct today: a manifest with `mold_use_authorized=True` is rejected. Deleting either clause (s01, s02) leaves all tests green. The same holds for the digest half of `is_exactly_scan_fitted` (line 100, s03), which gates ghosting, and for the combo-box ghost guard at line 188 (s05). The combo box is the real user path; only `set_mode` is tested. Add negative tests for these four guards.

**P2-4 (PL-0431). The ghost composite's cost is unbounded and it runs on every resize.** `_ghost_composite` (`design_review.py:288-307`) loops in Python over every pixel of both images with `pixelColor`/`setPixelColor`. `resizeEvent` (lines 182-184) calls `_refresh` with no throttling. Measured cost per composite: 0.54 s at 640×480 and **2.46 s at 1600×900**. A 4K window extrapolates to more than 10 s per resize event. Fix options:
- build the mask with `QPainter` composition modes, or with a NumPy view of the image bits;
- debounce the re-render on resize.

This breaks the project's bounded-cost rule once the widget is wired into a route.

**P2-5 (PL-0434). Nothing tests the visible disclaimer (criterion 4) or the visible provenance tags (criterion 2).** The test asserts `manifest["visible_disclaimer"]`, which is a module constant. With the `drawText(_DISCLAIMER)` call removed (d01), or with the `[provenance]` suffix removed from every field (d03), all 3 tests still pass. I confirmed the current behavior holds:
- Under the Windows QPA platform, the PDF text layer contains the full disclaimer, both IDs, the digest, all 16 field labels and every `[CLASSIFICATION]` tag.
- Under offscreen, red disclaimer glyphs are present in the rendered page (1925 px).

Regression protection for this safety label is missing. Add a test that extracts the text with `QPdfDocument.getAllText` when a font-backed platform is available, and falls back to a rendered-pixel or region check under offscreen. See P3-9 for why offscreen has no text layer.

### P3 (non-blocking)

**PL-0427 (`multi_ring_capture_recipe.py`):**
- P3-1: `create(..., starting_angle_degrees=-1e-20)` raises `recipe_identity_mismatch`, though the input is finite and valid. At line 106, `-1e-20 % 360.0 == 360.0`; `__post_init__` then re-normalizes that to `0.0` at line 83, and the digests disagree. Normalize once, or use `math.fmod` with a fix-up.
- P3-2: line 154, `round(angle, 9)`, can emit `360.0`. For example, a start of `359.9999999999` gives a first pose at 360.0, outside [0, 360).
- P3-3: line 109, `create((None,), 8)`, raises a bare `TypeError` instead of `MultiRingCaptureRecipeError`.
- P3-4: no test pins that pose IDs include `recipe_id` (m04). Today, two different recipes cannot share pose IDs, but nothing guarantees it.

**PL-0428:**
- P3-5: `AdaptiveAnglePlan` (line 102) is a public dataclass with no validation, so `AdaptiveAnglePlan("x", ...)` serializes a forged `plan_id`. The same pattern appears in other modules, so this is low risk.

**PL-0431:**
- P3-6: when ghost mode is rejected through the combo box (lines 189-193), the status label replaces the "REVIEW ONLY · NON-AUTHORITATIVE …" banner with "Ghosting unavailable…". The banner stays gone until the next resize or refresh, which I verified.
- P3-7: the caption "Design Model preview · <revision> · sha256:<preview digest>" (lines 235-240) presents a caller-supplied mesh under a Design Model revision ID. Nothing verifies the mesh against that revision (probe: an unrelated 4-vertex mesh is accepted and shows `EXACT_SCAN_MASTER_PARENT`). The Codex log discloses this, but the UI does not. Add a visible "caller-supplied preview; derivation not verified" qualifier.

**PL-0432 (`shelf_lineup.py`):**
- P3-8: `ShelfLineupPlan` and `ShelfLineupEntry` (lines 29-49) have public constructors with no validation, and the widget checks only `isinstance`. A plan with no entries makes `paintEvent` raise at line 179 (`max()` on an empty sequence), and a plan with `total_width_mm=0` kills the probe process. `gap_mm=10**400` raises `OverflowError` at line 63 instead of `ShelfLineupError`. The negative-gap rejection is untested (s09).

**PL-0433 (`supplier_comparison.py`):**
- P3-10: line 112, `f"{value.value:g}"`, keeps only 6 significant digits, in both the UI and `as_dict`. 123.4567 mm and 123.4574 mm both display as "123.457 mm", and 999999.5 mm displays as "1e+06 mm". With realistic packaging precision the impact is low, but the comparison can show two different supplier values as equal. Use `repr`, or the dossier's `{value}` formatting.
- P3-11: the asset count has no upper bound (line 57); I tested 300 columns. Non-`PackagingAsset` rejection is untested (s13). A supplier literally named "UNKNOWN" cannot be told apart from a missing one (line 114).

**PL-0434 (`packaging_dossier_pdf.py`):**
- P3-9: when no `QApplication` exists, the core exporter sets the process-wide `QT_QPA_PLATFORM=offscreen` (line 90) and creates one. In that mode the PDF has no font objects and no text layer: glyphs are drawn as paths and `getAllText` returns an empty string. So the "machine-readable PDF" goal in the prompt is met only when a font-backed platform is already running (Windows platform: Arial subsets with ToUnicode, full text). Disclose this, or embed the manifest JSON (for example as PDF metadata).
- P3-12: the PDF bytes are not deterministic: `/CreationDate`, `/ModDate` and `/ID` change on every call, so `pdf_sha256` differs between re-exports of the same asset. Everything else in the manifest is identical across calls. The criteria do not require this, but the manifest's digest cannot be reproduced. Either disclose it, or post-process the volatile keys.
- P3-13: the revision check at lines 66-69 is tautological, because `revision_id` and `canonical_json` are derived from the same object (d02). It is harmless, but it is not evidence of external identity verification.

## Rule checks (all six)

- **No physical, Kenya or factory claims.** All serializations carry explicit false flags (`physical_angles_observed`, `capture_performed`, `hardware_control_performed`, `scan_master_replaced`, `shelf_fit_certified`, `ranked`, `manufacturing_authorized`, `compliance_verified`), and the UI labels say "REVIEW ONLY", "SCHEMATIC", "DESCRIPTIVE" or "PACKAGING METADATA ONLY".
- **No authority upgrade.** Planned angles are `PLANNED_NOT_OBSERVED`, and 0428 complexity is labeled `CALLER_SUPPLIED_UNTRUSTED_NORMALIZED_SCORE`. Scan Master and Design Model inputs are not mutated (verified with `manifest_bytes()` and `revision_id` before and after). The only identity-labeling gap is P3-7.
- **No path or PII leakage.** Exports carry only `PackagingAsset` fields, which reject absolute paths and URIs. The PDF bytes contain no local path (searched for `Users` and the user name). The manifest carries free-text `source_description` fields (at most 160 characters) by design, as part of the source record.
- **Determinism.** Recipe, plan, lineup and comparison output is deterministic (checked with repeated calls). The exception is the PDF bytes (P3-12).
- **Licensing.** The 0427 and 0428 modules use stdlib only. The others use PySide6 6.11.2, an existing LGPL dependency already used in core by `technical_drawing_pdf.py`.
- **No hardware claims.** Nothing touches a camera, turntable, Bluetooth or the network. PL-0425 and PL-0426 hardware gates remain open.

**Feature flag and fallback (prototype tier).** None of the six has a flag, and none is wired into any route. The modules are inert unless explicitly constructed, and the fallback is the existing workflow. I accept that at prototype tier, on condition that the TASKS entries record "component only, not routed". `AppConfig.ai_assist_enabled` is not relevant, because these tasks are not AI. A Studio flag should be added when any of these is routed into the shell.

## Verdicts

| Task | Verdict | Basis |
|---|---|---|
| PL-0427 | **PASS** (`CLAUDE_PEER_AUDITED_PASS`-eligible, prototype tier; hardware and station gates PL-0425/0426 pending) | All 7 criteria verified by code reading, tests and probes. Only P3-1..P3-4. |
| PL-0428 | **CHANGES_REQUIRED** | P2-1: criterion 4 is violated by a reproducible probe. P2-2: five surviving mutants on criteria 1–3. Fixes are small (a minimum-width or post-check guard, plus about 5 tests). |
| PL-0431 | **CHANGES_REQUIRED** | P2-3: Scan Master authority and ghost guards are unpinned (4 surviving mutants). P2-4: the ghost composite takes about 2.5 s per resize at 1600×900. P3-6 and P3-7 are recommended in the same pass. |
| PL-0432 | **PASS** (prototype tier; owner SKU data and shell routing pending) | All 7 criteria verified. Only P3-8. |
| PL-0433 | **PASS** (prototype tier; live supplier data and routing pending) | All 7 criteria verified. P3-10 (`:g` rounding) is recommended but does not block. |
| PL-0434 | **CHANGES_REQUIRED** | P2-5: the visible disclaimer and provenance (criteria 2 and 4) are not covered by any test; mutants d01 and d03 survive. The current behavior is correct, as I verified. The fix is test-only, plus disclosure of P3-9 and P3-12. |

Scratch evidence (not committed): `probe_core.py`, `probe_studio.py`, `probe_studio2.py`, `probe_pdf*.py` and `mutate.sh` in the session scratchpad `.../scratchpad/m19/`.
