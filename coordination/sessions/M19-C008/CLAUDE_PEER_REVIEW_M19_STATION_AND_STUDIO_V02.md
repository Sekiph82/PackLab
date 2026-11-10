---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M19-C008 / M19-C009 / M19-C011 / M19-C014
version: 02
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: c5b80b265c63fdba13a8e91c354d2ec51c6b1390
respondsTo: CLAUDE_PEER_REVIEW_M19_STATION_AND_STUDIO_V01.md
tasks: [PL-0428, PL-0431, PL-0434]
tier: prototype
---

# Independent peer re-review V02: PL-0428, PL-0431, PL-0434 fixes (c5b80b26)

I did not write these fixes. I edited no source, test, doc or tracker file, and made no commit, push, stash, reset or branch switch. All probes and mutants ran from scratch scripts in the session scratchpad (`.../scratchpad/m19v2/`). Each mutant ran on a temporary copy of `core/src`, `apps/windows-studio/src`, `schemas`, the target test file and its own `pytest.ini`. The repository was never modified.

Inputs read: V01, `CLAUDE_IMPLEMENTATION_LOG_M19_STATION_STUDIO_FIXES_V01.md`, the frozen criteria (M19-C009 PL-0428, M19-C011 PL-0431, M19-C014 PL-0434), `git show c5b80b26`, and the full current versions of `adaptive_angle_plan.py`, `design_review.py`, `packaging_dossier_pdf.py` and their three test modules. HEAD moved to `783a0287` during review. The diff `c5b80b26..HEAD` over all in-scope source and test files, `viewport.py` and `tests/conftest.py` is empty.

## Commands and results

| Command | Result |
|---|---|
| `pytest -q` on adaptive_angle_plan, design_review, packaging_dossier_pdf, plus the 0427/0432/0433 modules (`QT_QPA_PLATFORM=offscreen`) | **55 passed** |
| The same two Qt test files under the default Windows QPA platform | 15 passed |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | Success: no issues in 288 source files |
| `git show --check c5b80b26` | clean |
| Hosted CI `gh run view 42892397185` (Windows Python Quality on `f2fb75e6`, which contains c5b80b26) | **success**, "2857 passed, 16 skipped, 1 deselected". Signing Material Guard run 42892397224 also succeeded. |

## Mutation results (temp copies)

| ID | Mutation | Result |
|---|---|---|
| m05 | 0428 score rounding `+0.5` removed | killed |
| m06 / m06a / m06b | 0428 coverage check removed / start-only / end-only | killed / killed / killed |
| m07 | 0428 duplicate sector-ID check removed | killed |
| m08 | 0428 `geometry_sha256` dropped from the plan identity | killed |
| m09 | 0428 geometry digest validation removed | killed |
| m10 | 0428 new narrow-sector `raise` removed | killed |
| m13 | 0428 `round(..., 9)` removed | killed |
| m11 | 0428 strict bounds weakened to `<=` | **survived** (P3-a) |
| m12 | 0428 distinctness clause removed | **survived** (P3-a) |
| s01 / s02 / s02b / s02c | 0431 manifest `authority_class` / `mold_use_authorized` / physical status / output digest clause removed | all killed |
| s03 | 0431 digest half of `is_exactly_scan_fitted` removed | killed |
| s05 | 0431 combo-box ghost guard removed | killed |
| s14 / s15 | 0431 refusal banner prefix removed / "unverified" caption removed | killed / killed |
| s16..s20 | 0431 composite: no mask, inverse mask, design layer dropped, same colour, wrong background key | all killed |
| d01 / d01b | 0434 disclaimer draw removed / truncated | killed / killed |
| d03 | 0434 `[provenance]` suffix removed | killed |
| d05 / d06 | 0434 field labels not drawn / revision not drawn | killed / killed |
| d07 | 0434 `_field_values` paints every provenance as `UNKNOWN` | **survived** (P2-6) |
| d07b | 0434 `_field_values` paints every provenance as `SUPPLIER_FACT` (authority upgrade) | **survived** (P2-6) |
| d08 | 0434 `_DISCLAIMER` reduced to `"PACKAGING METADATA ONLY. "` (all four non-claims gone) | **survived** (P2-6) |
| d09 / d10 | 0434 disclaimer drawn with a white pen / a zero rectangle | survived (P3-d) |

## PL-0428: V01 P2-1 and P2-2

- **The fix is correct.** `adaptive_angle_plan.py:170-179` rounds first, then fails closed with `sector_too_narrow_for_planned_angles` if any angle is not strictly inside its sector or if angles repeat. Open sector intervals are disjoint, so duplicates across sectors are impossible.
- **The V01 probe is now rejected.** Sectors `(0, 1e-12)` and `(1e-12, 360)` raise the new error.
- **Sweep.** I ran 20 000 seeded random plans: 1..8 sectors, uniform, clustered (widths 1e-13..1e-4) and near-0/360 cuts, a mix of fixed and random scores, and max-per-sector values of 1, 4, 8 and 64. Results: 12 401 accepted, 7 599 rejected as narrow, 0 other errors and **0 violations**. Every accepted plan has strictly-inside, globally distinct, strictly increasing angles in [0, 360) and an identical `plan_id` on repeat. 512 angles over a full circle are all distinct.
- **Edge cases** are rejected as intended:
  - a strictly-inside duplicate produced by 9-decimal rounding: sector `(1.0000000004, 1.0000000034)` with 4 angles gives `…001, …002, …002, …003`;
  - a single angle that rounds onto 360.0.
- **P2-2 is closed.** m05..m09 are all killed. The rounding table matches the V01 probe values.
- **P3-a (non-blocking), `tests/core/test_adaptive_angle_plan.py:76-83`.** The only narrow-sector test has angles that are both on the boundary and duplicated, so m11 and m12 survive. The two edge cases above would pin each clause separately.

**Verdict: PASS.** `CLAUDE_PEER_AUDITED_PASS`-eligible, prototype tier. It is a component only and not routed. Station and hardware gates stay pending.

## PL-0431: V01 P2-3, P2-4 and P3-6/7

- **P2-3 is closed.** The parametrized manifest test (`test_design_review.py:177-193`) covers all four authority/identity clauses. The digest-mismatch test (`:196-206`) and the combo-box test (`:209-221`) kill s01..s05. The forged stale model uses `object.__setattr__`, which is acceptable as test-only defense in depth.
- **P2-4 is closed.** I checked equivalence against a verbatim copy of the pre-fix per-pixel loop.
  - **Pixel-exact match: 0 differing pixels.** The inputs were real `QtRasterViewportAdapter` renders through the widget's own `_render_source` with a common camera: three scenes (overlapping triangle, offset triangle, tetrahedron) at 320×200 and 641×479. These include antialiased edges (up to 413 distinct colours) and both layers. Rendered alpha is always 255 (`viewport.py:518-519` fills opaque).
  - **Premultiplied input** gives an identical result.
  - **Timing (offscreen):** 4.5 ms at 640×480, **17 ms at 1600×900** (was 2.46 s), and 103 ms at 3840×2160. A widget resize in ghost mode takes about 35–44 ms. The in-test bound of 0.5 s leaves a margin of about 30× on hosted runners.
- **P3-6 and P3-7 are closed.** The refusal text keeps "REVIEW ONLY · NON-AUTHORITATIVE", and the caption says "caller-supplied, unverified". Both are pinned (s14 and s15 are killed).
- **P3-b (non-blocking), `design_review.py:300-306`.** The binary mask drops the old per-pixel alpha behaviour. A semi-transparent source pixel now gets full layer colour (a 2-pixel synthetic diff, max channel delta 133), and an alpha-0 non-background pixel is now painted. This cannot happen through the opaque adapter, but the docstring should state the opaque-input assumption.
  - The implementation log says the composite is "checked pixel by pixel against the background and geometry". The test actually checks 3 pixels. Pixel equivalence is established by this review, not by the test.
- **P3-c (non-blocking, pre-existing, not introduced by this fix).** The status label and captions are unwrapped single lines carrying two 64-hex digests, so the widget's `minimumSizeHint` width is about 4654 px. This needs word wrap or elision before the widget is routed into the shell.

**Verdict: PASS.** `CLAUDE_PEER_AUDITED_PASS`-eligible, prototype tier. It is a component only and not routed. The preview mesh remains caller-supplied and unverified, which the UI now discloses.

## PL-0434: V01 P2-5

- **Partly closed.** The new test (`tests/core/test_packaging_dossier_pdf.py:143-166`) wraps `QPainter.drawText` at the Python level and records the real painted strings. This does not depend on the platform: it passes both offscreen and under the Windows QPA platform, and in hosted CI. It kills d01, d03, d05 and d06, which is a real improvement. The current painted output is correct: for example, `'UNKNOWN  [UNKNOWN]'` for the empty weight and `'180.0 mm  [SUPPLIER_FACT]'`.
- **P2-6 (blocking), `tests/core/test_packaging_dossier_pdf.py:146,160-165`. The test oracle is the code under test.** The test builds its expectations from the module's own `_DISCLAIMER` and `_field_values`, so it repeats V01's "test checks a constant" problem one level down.
  - d07b changes `packaging_dossier_pdf.py:239` so that every field is painted `[SUPPLIER_FACT]`. That includes fields recorded as `UNKNOWN`, which is a visible provenance authority upgrade. All 4 tests stay green.
  - d08 strips every non-claim from `_DISCLAIMER` (lines 32-35), contrary to criterion 4. All tests stay green, because the only literal check is "PACKAGING METADATA ONLY" in the manifest.
  - **Fix (test-only):** assert literal expected painted strings for a few fixture fields, e.g. `"Synthetic bottle  [USER_DECLARED]"`, `"180.0 mm  [SUPPLIER_FACT]"`, and `"UNKNOWN  [UNKNOWN]"` for `empty_package_weight`. Also assert that the painted disclaimer literally contains "physical accuracy", "supplier certification", "regulatory compliance" and "manufacturing authorization".
- **P3-d (non-blocking).** Recording `drawText` cannot show that the text is visible (d09 white pen and d10 zero rectangle survive). V01's suggested offscreen check for red disclaimer pixels in the rendered page would close this. It is optional.
- V01 items P3-9 (no text layer under offscreen) and P3-12 (non-deterministic PDF bytes) remain disclosed as not addressed. That is acceptable at prototype tier.

**Verdict: CHANGES_REQUIRED.** One small test-only change (P2-6). Behaviour is correct today. A narrow re-review of the test file is sufficient.

## Verdicts

| Task | Verdict |
|---|---|
| PL-0428 | **PASS** (`CLAUDE_PEER_AUDITED_PASS`-eligible, prototype tier; station/hardware gates pending). P3-a only. |
| PL-0431 | **PASS** (`CLAUDE_PEER_AUDITED_PASS`-eligible, prototype tier; not routed). P3-b and P3-c only. |
| PL-0434 | **CHANGES_REQUIRED**. P2-6: the self-referential oracle lets provenance-upgrade (d07b) and disclaimer-content (d08) mutants survive. Test-only fix. |

No P0 or P1 findings. Scratch evidence (not committed) is in the session scratchpad `m19v2/`: `probe_composite.py`, `probe_ratchet.py`, `sweep_0428.py`, `probe_pdf_drawn.py` and `mutate2.py`.
