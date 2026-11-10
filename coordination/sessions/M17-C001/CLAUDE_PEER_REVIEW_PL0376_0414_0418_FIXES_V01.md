---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001 / M18-C001
version: 01
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: 727bedbf7caf2b751777c5e8a438f3cca0fa46db
respondsTo:
  - coordination/sessions/M17-C001/CLAUDE_PEER_REVIEW_PL0375_0378_V03.md
  - coordination/sessions/M18-C001/CLAUDE_PEER_REVIEW_M18_CHANGE_PROCESSES_V01.md
tasks: [PL-0375, PL-0376, PL-0414, PL-0415, PL-0416, PL-0417, PL-0418]
---

# Independent peer re-review: fixes in 727bedbf (PL-0376, PL-0414, PL-0418)

I did not implement this work. I edited no source, test, tool, doc or tracker file, and I did not commit, push, stash, reset or switch branches. All probes and mutants ran from scratch scripts in the session scratchpad. Mutants were loaded in memory (constant patching, or module substitution under the real module name); the repository was never edited.

## Scope

- Commit `727bedbf` "fix(pl-0376,pl-0414,pl-0418): address independent review findings": 15 files, +779/−60.
- I read in full: the two review reports it responds to; `git show 727bedbf`; `core/src/packlab_core/rescan_decision.py`; `tools/dev/scan_copy_manifest.py`; `tools/datasets/calibrate_object_texture.py`; the texture section of `core/src/packlab_core/pre_reconstruction_qa.py` (guard at lines 34–36, 201–248) and its component aggregation (lines 722–785); `tests/core/test_object_surface_texture_qa.py`; `tests/core/test_rescan_decision.py`; `tests/ci/test_scan_copy_manifest.py`; the five PL-0414..0418 docs; the PL-0375 calibration doc; and the frozen criteria for PL-0375, PL-0376, PL-0414 and PL-0418.
- `HEAD` moved to `ef5eb681` (later PL-0394/0395 commits) during the review. `git diff 727bedbf HEAD` over every in-scope file is empty. The only changed file under `docs/development` is `V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md`, which is out of scope. The working tree has unrelated uncommitted M19 edits that I did not touch.

## Commands and results

| Command | Result |
|---|---|
| `pytest -q` on the 8 requested files (`QT_QPA_PLATFORM=offscreen`) | **157 passed** in 51 s |
| `ruff check core apps tools tests` | All checks passed |
| `mypy core apps tools` | Success: no issues found in 288 source files |
| `gh run view 42885936327` (Windows Python Quality, head `727bedbf`) | completed / **success** |
| `gh run` 42885936264 (Signing Material Guard, `727bedbf`) | completed / success |
| `python -m tools.datasets.calibrate_object_texture` | 64 rows. Plain: 32 rows, max **0.0643** (PP closure, σ 10), all `warning`. Labelled: 32 rows, min **0.1730** (HDPE trigger spray, σ 10), all `pass`. Both match the doc table. |
| The prior reviewer's `probe_specular.py` (re-run against v2) | All 18 streak cases on the bottle, tube and jar give `warning`, textured fraction ≤ 0.007. P2-7 as originally probed is resolved. |

Scratch probes: `rv_spec.py`, `rv_spec2.py`, `rv_rescan.py`, `rv_copy.py`, `rv_mut.py`, `rv_mut_rescan.py`.

### Texture mutants (in-memory constants; texture + rescan tests, 47 tests)

| Mutant | Result |
|---|---|
| Halo 0 | killed (4 failed) |
| Halo 4 | killed (2) |
| Guard off (17 samples) | killed (13) |
| Specular min samples 8 | killed (1) |
| Threshold 0.05 / 0.09 / 0.15 / 0.25 | all killed (1 / 1 / 2 / 2). This closes P3-2 from V03. |
| Halo 1 | **survived** |
| Specular DN 250 | **survived** |

### Rescan source mutants (`test_rescan_decision.py`, 24 tests)

- R2–R9, R11 and R12 are each killed. They cover the photos requirement, the overall check, the all-pass gate, turntable → `full_rescan`, ignoring missing metadata, ignoring minority texture, dropping the exposure retake, targeting with empty sectors, accepting malformed counts, and `conclusive = True`.
- R10 (removing the unknown-status rule) **survived**. It is effectively equivalent: the `conclusive` gate still prevents `proceed`, and only the reason code changes. This also closes the prior reviewer's surviving mutants (a), (c) and (d).

## PL-0376 / PL-0375: specular guard probes

All probes are seeded and synthetic, using the M17 renders, the masks and the simulated streak helper with its `level` parameter. "Pass" means `object_surface_texture: pass`.

| Probe | Result |
|---|---|
| Clipped (≥ 240) streaks: 1–3 streaks, 1–12 px wide, soft edges 0–8 px, σ 0–12 | All `warning`. Max fraction 0.0084 (seed 3) and 0.0100 (seed 2). |
| Thin 1-px diagonal clipped lines (5 slopes) | All `warning` |
| Random glints (1 px, 1×2, 1×3, 2×2 at 255), density 0.2–2 % | All `warning` (max 0.07) |
| **Streak core below 240 DN**, tube, σ 3 | `pass` at 225 / 230 / 235 DN (0.14–0.34). The halo only applies from about 238 DN, where noise pushes samples to ≥ 240. |
| **Streak core 239 DN**, bottle, σ 0, 2×6 px | `pass` 0.125. **All five components `pass`, overall `no_automated_concern`, and PL-0414 gives `proceed_to_reconstruction_review`.** At 236 DN it is `warning` (0.06). With σ 3 it is `warning`. |
| **Dark environment-reflection bands** (unclipped, 40–140 DN), bottle and tube, σ 3 | Bottle: `pass` 0.16–0.30. Tube: `pass` 0.13–0.55. On the bottle with one 4-px band at 40 DN: **all components `pass`, overall `no_automated_concern`, and PL-0414 gives `proceed_to_reconstruction_review`.** The clear jar stays `warning`. |
| Cell-aligned 3-of-16 glints on every other cell (adversarial upper bound) | `pass` 0.16–0.28 at stride 2; `warning` at strides 3 and 4. This is contrived, not realistic. |
| The tube's overall result | Its sub-240 passes still end up `review_required`, but only because the plain tube render already has an unrelated `pixel_exposure` warning (mean luma 221.8 > 215). The texture component alone is not what protects it. |

False warnings on labelled objects. To get v1 behaviour, I disabled the guard in memory and compared:

| Case | v1 (guard off) | v2 |
|---|---|---|
| Calibration labels (all 32 rows) | all `pass` | all `pass`; minimum falls from 0.1906 to 0.1730 (trigger spray σ 10, which has 7 % of mask pixels ≥ 240) |
| Labelled bottle, 1 streak | `pass` | `pass` 0.15 |
| Labelled bottle, 2 streaks across the label | `pass` 0.40 | **`warning` 0.07** |
| Labelled bottle, 3 streaks across the label | `pass` 0.48 | **`warning` 0.02** |
| Labelled tube, 1 streak across the label | `pass` 0.34 | **`warning` 0.09** |
| Labelled white surface brightened ×1.2–1.3 | — | can flip to `warning`, but the global clipped-pixel exposure warning already fires in every such case (29–97 % > 239) |

The labelled-object warnings are conservative. However, at ≥ 50 % of views PL-0414 routes them to `surface_treatment_review` ("retaking photos alone will not add texture").

PL-0375 regression after v2:
- The HDPE matte low-texture warnings, the printed-label `pass` (σ 0 and 10) and the ±5 DN noise probe are all still pinned by passing tests.
- The guard can only remove textured cells, so v2 cannot turn a plain-render warning into a pass.
- The labelled margin is 0.053 above the threshold (≥ 0.04 is pinned in CI).

## PL-0414 probes (`rv_rescan.py`, about 60 payloads)

**Now safe.** None of these reach `proceed`; each gives manual review, stop, or `RescanDecisionError`:

- Every payload from the prior reviewer:
  - empty or missing components;
  - a non-dict component;
  - `coverage: failed` and `metadata: warning`;
  - empty or non-mapping photos;
  - `overall: review_required` or a missing `overall`;
  - texture 1/4, bool counts and `low > assessed`;
  - an unknown or missing recapture decision;
  - `targeted_recapture` with no sectors;
  - NaN, bytes and a nested `MappingProxyType`.
- New payloads:
  - `overall` not a mapping;
  - status `True`;
  - float, negative or huge counts;
  - `inf`;
  - a non-str key;
  - a coverage warning with no mode;
  - a guided-orbit coverage warning combined with metadata `failed`.
- With the real producer:
  - missing `photos.json` → `stop_reimport_source` / `photo_metadata_missing`;
  - a clean 36-frame turntable → `manual_review` / `coverage_needs_session_level_check`;
  - a known sector gap → `targeted_recapture` on `az05-el00`.

**Still reach `proceed`**, each only with a hand-edited or contradictory report. The real producer cannot emit any of them: `pre_reconstruction_qa.py:722-785` derives every component from the per-photo statuses, and any unavailable photo makes the component unavailable.

- `photos: [{}]`
- a per-photo `sharpness` of `unavailable` or `failed` while the components are `pass`
- a per-photo texture `warning` while the component is `not_requested`
- texture `pass` with counts 0/0, or with no evidence
- an extra, unknown component that is `failed`
- `no_recapture_indicated` together with a non-empty `suggestions` list

The documentation matches the code. The rule-1 through rule-7 table matches the order of `ACTIONS` and the reason codes. Rule 7's "at least one photo was assessed" is slightly stronger than the code, which only requires a mapping entry (see P3-B).

## PL-0418 probes (`rv_copy.py`, real `mklink /J` in the scratchpad)

**Refused / FAIL (correct):**

- copy root is a junction to the source;
- a nested junction at depth 1 and at depth 2;
- `create` from a junction root (CLI exit 1).

**Invalid (correct):**

- an empty source (`create` refuses);
- `files: []` with counts of 0;
- a wrong `file_count` or `total_bytes`;
- a missing `file_count`;
- a non-dict entry, a missing key, a non-str path, a bool size, or a duplicate path;
- a top-level `[]`, `"x"`, `None` or `3`.

Invalid manifest JSON gives an uncaught `JSONDecodeError` and exit 1, which fails closed.

I could not create symlinks: `os.symlink` returns WinError 1314 (no privilege). The CI test falls back to symlinks only where junctions are unavailable.

**Still PASS wrongly:**

- **Copy root reached through a junctioned ancestor.** I created `jparent → scans`, then verified `jparent\src`. That root is not a junction itself, but `realpath` equals the source: **`SCAN_COPY_VERIFY_PASS`**.
- **Unreadable subdirectory at `create`.** `os.walk(..., onerror=None)` silently skips a directory whose `scandir` raises. I simulated `PermissionError` on `captures/deep`. The manifest silently omits `captures/deep/b.bin`, and a copy that also lacks that subtree then gives **PASS**.
- Hard-linked copy on the same volume: PASS (same physical data).
- Verifying the source itself: PASS. The prior reviewer classed this as procedural.
- An extra empty directory in the copy: PASS (known F11).

## Findings

### P0 / P1

None.

### P2

**P2-A (PL-0376). The specular guard is a hard ≥ 240 DN gate, so unclipped specular reflections still count as texture and can produce an all-pass result for plain glossy PET.**

- Where:
  - `core/src/packlab_core/pre_reconstruction_qa.py:34-36, 213-220, 241-243`
  - calibration doc lines 40–52 and 61–70
- Evidence:
  - A bottle with a 239 DN core and no noise, or a bottle with an unclipped dark reflection band, gives `no_automated_concern` on all five components. PL-0414 then gives `proceed_to_reconstruction_review`.
  - Tube highlights at 225–235 DN with σ 3 give texture `pass`.
- Glossy PET reflects the environment in both directions:
  - dark flags or backdrops give dark bands;
  - capture with exposure set to avoid clipping (which the station's exposure rule encourages), or HDR tone mapping, gives highlights below 240.
- So this is the same failure class as P2-7, with different parameters.
- The doc says "PL-0376 relies on the low-texture warning plus the specular guard". It also says "the specular guard prevents false texture". It does not say that highlights below 240 DN or dark or environment reflections are outside the guard.
- `V1_LIMITATIONS_AND_MANUFACTURING_BOUNDARY.md:16` mitigates this in general terms, but not specifically.
- Criteria: PL-0376 criterion 2, in the same spirit as V03's treatment of P2-7.
- Minimum fix:
  - State the limit explicitly in the calibration doc and the PL-0376 evidence: the guard covers only highlights ≥ 240 DN; reflections below 240 DN and dark reflections can still yield `pass` / `no_automated_concern` on glossy PET.
  - Pin that known limit with a test (for example, a 239 DN bottle at σ 0, or a dark band), so a future change is visible.
  - Preferred: a relative bright-cell rule, for example cells well above the object's masked median or 95th percentile luma.
  - Dark reflections cannot be told apart from print on a single grey frame. That is why the disclosure is the essential part.

**P2-B (PL-0418). A copy root reached through a junctioned ancestor, or a source with an unreadable subtree, still yields `SCAN_COPY_VERIFY_PASS`.**

- Where:
  - `tools/dev/scan_copy_manifest.py:29-35`
  - `docs/development/PL-0418_SCAN_BACKUP_POLICY.md:37`, which says "including a copy root that links back to the source"
- The ancestor case is F5 moved up one directory level.
- The unreadable-subtree case is a silent omission from the manifest. `os.walk` ignores errors by default, so the sample can be released while those files were never backed up.
- The policy releases the physical sample on PASS, and that cannot be undone.
- Minimum fix:
  - `os.walk(root, onerror=<raise>)`.
  - Refuse when `os.path.realpath(root) != os.path.abspath(root)`. This catches any reparse point in the ancestor chain.
  - Optionally record the source `realpath` and volume (`st_dev`) in the manifest, and refuse or warn when the copy is on the same volume. That also covers hard links and verifying the source itself, and it matches the policy's "2 media".
  - Alternatively, correct the doc claim and add an explicit SOP step: verify on the destination machine or media only.

### P3 (non-blocking)

- **P3-A (PL-0376).** Halo-1 and DN-250 mutants survive. The tests do not pin the halo radius or the 240 level.
- **P3-B (PL-0414).** `conclusive` does not cross-check per-photo statuses, texture `assessed_image_count > 0`, unknown extra components, or `suggestions` against `no_recapture_indicated`. A hand-edited report can still reach `proceed` (cases listed above). The real producer cannot.
  - Rule 7's "at least one photo was assessed" is stronger than `bool(photos)`.
  - `targeted_recapture` accepts `sector_id: ""`.
  - A photo with a warning and no `image_path` is listed as `"None"`.
- **P3-C (PL-0376).** Calibration doc accuracy:
  - The doc row "≤ 0.007" for the 24 streak rows: I measured max 0.0084 with the test's seed 3 (0.0100 with seed 2). It is still all `warning`.
  - These rows are not produced by the CLI that the doc names as the reproduction command.
  - "A labelled PET bottle beside a highlight still passes" holds only for one streak on the wide bottle. Two or more streaks across a label, or one on the tube, give `warning`. That increases false warnings on labelled glossy objects, and PL-0414 may then route them to `surface_treatment_review`. This should be disclosed.
- **P3-D (PL-0414).** The unknown-status rule (R10) is shadowed by the `conclusive` gate. Its reason code is not asserted.
- **P3-E (PL-0418).** Empty directories are still not recorded (F11). Symlink detection could not be exercised on this host (WinError 1314). Junctions were exercised.
- The open items from V03 are now disclosed in the calibration doc: P3-1 (noise ceiling) and P3-3 (mask tightness). P3-4 and P3-6 remain as disclosed.

## Doc-only notes PL-0415 / 0416 / 0417 (F8–F10)

All three notes are accurate against the code the prior reviewer cited, and each states a reviewer check:

- PL-0415 §6: nothing refuses deletion, so the reviewer runs `validate_targets` first.
- PL-0416 §3: the contract does not bind the label zone to the asset's Design Model.
- PL-0417 §4: `with_source_links` does not check the Design Model's parent Scan Master.

Remaining gaps, all P3 and not blocking (those tasks are already PASS):

- The F8 sub-points are not addressed in the docs:
  - `USER_DECLARED` is accepted for supplier fields;
  - the test name contradicts its semantics;
  - a rollback fails with `packaging_sku_revision_duplicate`.
- The F9 tautology test is unchanged.

## Verdicts

| Task | Verdict | Basis |
|---|---|---|
| PL-0375 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | The HDPE warnings, printed-label pass and noise probe still hold under v2. The calibration table is reproduced exactly. Threshold mutants are now killed. |
| PL-0376 | **CHANGES_REQUIRED** | P2-7 as originally probed (clipped streaks) is resolved and pinned. P2-A: unclipped glossy reflections (below 240 DN, or dark bands) still produce an undisclosed all-pass / `proceed` for plain glossy PET. It clears with the explicit disclosure plus a pinned known-limit test; an algorithm change is preferred but optional. |
| PL-0414 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | F1–F4 and F6 are fixed and tested. No producer-reachable path to `proceed` without positive evidence. Mutants are killed except the equivalent R10. P3-B and P3-D remain. |
| PL-0418 | **CHANGES_REQUIRED** | F5 root and nested junctions, F7 and F11 malformed manifests are fixed and tested. P2-B: an ancestor junction or an unreadable source subtree still gives `SCAN_COPY_VERIFY_PASS`, and the doc overclaims. Either a small code fix or a corrected doc claim plus an SOP step clears it. |
| PL-0415 / 0416 / 0417 doc notes | **Accurate** | The F8, F9 and F10 notes are correct reviewer-check statements. The minor F8 sub-points remain (P3). |

Hosted CI for `727bedbf` is green (run 42885936327). Nothing here is physical, factory, Kenya or real-capture validation. Every fixture is synthetic, and those gates stay open.
