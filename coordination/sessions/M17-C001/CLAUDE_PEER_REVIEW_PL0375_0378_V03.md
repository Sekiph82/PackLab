---
coordinationSchema: packlab-coordination/v1
artifactType: claude-peer-review
cycleId: M17-C001
version: 03
actor: CLAUDE_INDEPENDENT_REVIEWER
reviewedCommit: 28c185e4d4382ca3f0d4bbf8010c4375799769da
supersedes: CLAUDE_PEER_REVIEW_PL0375_0384_V02.md (PL-0375, PL-0376 and PL-0378 verdicts only)
tasks: [PL-0375, PL-0376, PL-0378]
---

# Independent peer re-review V03: PL-0375 / PL-0376 / PL-0378 (commit 28c185e4)

I did not implement this work. I edited no source, test, tool or tracker file. All probes and mutations ran on
scratch copies in my temp directory.

## Scope

- Commit `28c185e4`: "noise-robust object texture QA and known-missing-sector tests". It changes 7 files (+636/−5):
  - `core/src/packlab_core/pre_reconstruction_qa.py`
  - `apps/windows-studio/src/packlab_studio/pre_reconstruction_qa.py`
  - `tools/datasets/calibrate_object_texture.py`
  - `tests/core/test_object_surface_texture_qa.py` (new)
  - `tests/core/test_recapture_sector_suggestions.py` (+3 tests)
  - the implementation log V02 and the calibration doc
- `HEAD` moved to `08ed55e2` (PL-0414..0418) while I was reviewing. I checked with `git diff 28c185e4 08ed55e2` that every in-scope file is byte-identical between the two, so all results below apply to `28c185e4`.
- The working tree has unrelated staged and unstaged changes (`.github/workflows/_coordinator_pl0005_close.yml` deleted, `.gitignore` modified). I did not touch them.

## Commands and results

| Command | Result |
|---|---|
| `pytest -q tests/core/test_object_surface_texture_qa.py tests/core/test_pre_reconstruction_qa.py tests/core/test_recapture_sector_suggestions.py tests/core/test_photo_duplicates.py` (`QT_QPA_PLATFORM=offscreen`) | 41 passed in 11.45 s |
| `ruff check core apps tools tests` | All checks passed! |
| `mypy core apps tools` | Success: no issues found in 286 source files |
| `python -m tools.datasets.calibrate_object_texture` | 64 rows. Plain: 32 rows, min 0.0000, max **0.06804** (PP closure, σ 10), all `warning`. Label: 32 rows, min **0.19064** (PET tube, σ 3), max 0.3202, all `pass`. This matches the calibration doc table (0.0680 / 0.1906 / threshold 0.12). |
| Hosted CI, run 42881593961 (head `28c185e4`, Windows Python Quality) | completed / success: ruff clean, mypy 286 files, "2624 passed, 16 skipped, 1 deselected" |

Probe scripts (scratch): `probe_texture.py`, `probe_specular.py`, `probe_overall.py`, `mutate.py`, `mutate2.py`, `bc.py`.

### Adversarial probes on the texture detector

| Probe | Result |
|---|---|
| Plain renders + Gaussian noise σ 12, seeds 1–4 | All `warning` on all 5 tested renders |
| σ 15 | PP closure: `pass` on 3 of 4 seeds (0.12–0.14). Others: `warning`. |
| σ 18 | HDPE jerrycan, PET bottle and PET tube: `pass` on seed 1 (0.125–0.137). PP closure: `pass` on all seeds. |
| σ 20 / 25 | Most renders `pass` (0.12–0.30) |
| Flat 128² surface at 200 DN | σ 18: `warning` 0.109. σ 20: `pass` 0.13. |
| Genuine low-contrast 8 px checker | ±4 DN: `warning` (conservative direction). ±8 DN or more: `pass`. |
| JPEG q 20 / 50 / 85 on plain renders, σ 0–10 | All `warning` (no blocking-artefact false pass) |
| Label seed sensitivity (seeds 1–20) | Min fraction 0.194 (tube). The negative case is stable. |
| Full-frame mask on plain renders | All `warning` (0.006–0.046) |
| Jerrycan mask dilated by 2 / 4 / 8 px | `warning` |
| Jerrycan mask dilated by 16 px | `pass` 0.139 (silhouette leak with a grossly loose mask) |
| 1-px-wide mask, all-zero mask, 1×1 image, holes every 8 px | `unavailable` / `object_area_too_small` (fail-closed) |
| Mask bytes 0xFF or 0x02 | Treated as inside, as documented |
| 63×61 (non-multiple of 4) | Handled |
| Invalid inputs: bytearray, width 0, bool width, empty or 65-char id, 1001×1000 | All rejected with `PreReconstructionQAError` |
| Non-mask value in the mapping | `object_mask_invalid` |
| 1000×1000 full mask | 0.31 s |
| **Specular streaks (simulated) on glossy PET**: 1–3 vertical clipped (255 DN) highlight streaks, 6 px wide, along the body inside the mask, + σ 3 noise | Bottle with 2 streaks: texture **`pass` 0.209**. Tube with 1 streak: **`pass` 0.197**. Global >239 fraction is 1.4% / 0.3%, so the exposure rule does not fire. Soft-edged streaks (w 4, 4 px ramp): still `pass` (bottle 0.173, tube 0.385). Wide soft streaks (w 12, 8 px ramp): `warning`. The clear PET jar stays `warning`. |
| Full QA on the bottle with 2 streaks (via `build_pre_reconstruction_qa` with masks) | **All five components `pass`; overall `no_automated_concern`, `next_action: continue_workflow_review`** |

### Mutation testing (scratch copies only, loaded ahead of the editable install; module path verified)

PL-0378, against `-k pl0378` (3 tests):

| Mutant | Result |
|---|---|
| M1: occupied sectors not excluded | 3 failed (killed) |
| M2: azimuth index off by one | 3 failed (killed) |
| M3: ascending gap sort | 1 failed (killed) |
| M4: mirrored azimuth (`atan2(-y, x)`) | 2 failed (killed) |
| M5: wrong start bound | 1 failed (killed) |
| M6: only the first suggestion kept | 1 failed (killed) |

Texture detector, against `test_object_surface_texture_qa.py` (9 tests):

| Mutant | Result |
|---|---|
| T1: block size 1 (no noise averaging) | 6 failed (killed) |
| T3: component dropped from the overall result | 4 failed (killed) |
| T6: mask ignored | 3 failed (killed) |
| T2: neighbour-inside requirement removed | **survived** |
| T4: threshold 0.12 → 0.05 | **survived** |
| T5: threshold 0.12 → 0.25 | **survived** |

### Backward compatibility (parent `28c185e4^` vs `28c185e4`, no masks)

I ran the jerrycan, PET bottle and PP closure at σ 4, plus a decode-failure case. After removing only the additive keys, the outputs are identical:

- the `object_surface_texture` component
- the two `thresholds` entries
- the per-photo `object_surface_texture`

Overall status is unchanged in every case (`no_automated_concern` ×3, `incomplete` ×1). The new component reports `not_requested`. That status is not counted by the overall rule (`pre_reconstruction_qa.py:751-757`), so behaviour without masks is unchanged. The schema id stays `packlab.pre-reconstruction-qa.v1` even though fields were added. That is additive, and no pinned digest exists in the tests.

## Findings

### P0 / P1

None.

### P2

**P2-7 (PL-0376). Specular highlights count as surface texture.** This turns the glossy-PET low-texture warning into a pass, and the PL-0376 test cannot detect it.

- Where:
  - `core/src/packlab_core/pre_reconstruction_qa.py:212-216`
  - `tests/core/test_object_surface_texture_qa.py:108-122`
  - `coordination/sessions/M17-C001/PL-0375_OBJECT_TEXTURE_CALIBRATION_V01.md:54-57`
- What the code does: the block Laplacian counts any block-scale luminance step inside the mask, including clipped specular streaks.
- Why the test cannot catch it:
  - The PL-0376 fixtures are AgX-tone-mapped renders that "barely clip" (the test even asserts `< 0.05` clipping).
  - As a result, the PL-0376 test exercises the same mechanism as the matte HDPE test. It would pass unchanged if the renders were matte, so it does not exercise the glossy failure mode at all.
- What the probe shows: one or two narrow clipped streaks are the typical appearance of a glossy cylindrical bottle under strip or softbox lighting. They are enough to give `object_surface_texture: pass`, and the PET bottle then gets overall **`no_automated_concern` / `continue_workflow_review`** with every component passing.
- Downstream impact: `rescan_decision.py` (PL-0414, `08ed55e2`) would then emit `proceed_to_reconstruction_review` for a glossy, unlabelled PET.
- The calibration doc says PL-0376 "relies on the low-texture warning". It describes the gap only as "cannot calibrate a specular-clipping detector". It does not disclose that the specular condition itself defeats the warning PL-0376 relies on.
- Criteria affected: criterion 1 (the fixture must exercise the *relevant* gate) and the contract's negative-case requirement. In spirit, it also affects criterion 2: the specular limitation produces an unsupported "no concern" result.
- Suggested minimal fix:
  - Exclude or flag blocks containing near-clipped samples (≥ 240 DN, the existing `overexposed_pixel_fraction_above_239` level) from the textured count.
  - Report a masked specular fraction. Warn, or mark the result unavailable, above a small threshold.
  - Add a seeded, provenance-labelled specular-streak negative fixture for PET gloss. It can be simulated like the printed label, or rendered with a non-AgX/Standard view transform. Assert that it is never `pass` / `no_automated_concern`.
  - Update the calibration doc accordingly.

### P3 (non-blocking; record and track)

- **P3-1. The noise ceiling is undisclosed while the commit claims "noise-robust".**
  - Where: `pre_reconstruction_qa.py:216`; calibration doc lines 32-33 and 53.
  - The detector is robust up to about σ 12 DN on all fixtures. PP closure flips to `pass` at σ 15. Most renders flip at σ 18–20, which is also the analytic crossover: the response std is √20·σ/4, against a threshold of 32 DN.
  - Heavy noise errs toward a **false pass**, the opposite of the doc's "errs toward review" note, although that note is literally about fine texture.
  - σ 10 is already called "deliberately pessimistic", so this does not block PL-0375. The doc should state the measured ceiling, and ideally a noise-floor estimate should mark views above it `unavailable`.
- **P3-2. The calibration is not regression-pinned in CI.**
  - Where: `tests/core/test_object_surface_texture_qa.py`.
  - Thresholds of 0.05 and 0.25 both pass the suite (T4, T5), and removing silhouette exclusion passes too (T2).
  - The 8-sample × 4-σ table lives only in the CLI tool. A test over `calibration_rows()` would pin it: plain max < 0.12 ≤ label min, and the PP closure at σ 10 stays `warning`. A loose-mask case would pin the 4-neighbour rule.
- **P3-3. Mask tightness is an unstated assumption.**
  - Where: `pre_reconstruction_qa.py:204-212`.
  - A mask dilated by 16 px yields a `pass` from silhouette and backdrop edges. Masks dilated by ≤ 8 px are fine.
  - The doc should state that masks must be tight, segmentation-quality object masks.
- **P3-4. The production Studio flow is inert for now.**
  - Studio does not yet supply masks, so a real low-texture HDPE capture still gets `no_automated_concern` without masks. I confirmed this for the jerrycan at σ 4, identical to the parent commit.
  - The log and doc disclose this. Tracker wording should not imply production protection.
  - Masks must also match the *decoded sample* dimensions after the adapter's nearest-fit-1024 scaling. A mismatch is fail-closed (`object_mask_dimension_mismatch`).
- **P3-5. The PL-0378 synthetic poses use identity rotations.**
  - Where: `test_recapture_sector_suggestions.py:122`.
  - Cameras are not oriented toward the object. The module uses only camera centres, so this does not affect validity, and the docstring disclaims physical poses.
  - It is still not a physically plausible capture rig in the contract's sense.
- **P3-6. Speckled masks make the whole view `unavailable`.** A mask with holes every 8 px leaves no assessable cells. This is fail-closed, so it is acceptable, but real segmentation noise could make the check routinely unavailable.

### Prior findings status

| Finding | Status | Evidence |
|---|---|---|
| P2-2 (PL-0375) | **Resolved** | A noise-robust masked detector on provenance-bearing M17 renders. The reviewer's ±5 DN probe now warns (fraction 0.0). There is a seeded printed-label negative case. Calibration is reproducible. There is no physical claim. |
| P2-3 (PL-0376) | **Provenance part resolved** | The fixtures now come from the manifest-backed M17 subset (generator 2.0.0, seed 3692026, camera, lighting and material recorded, `fully_synthetic: true`). A new P2-7 is open: the glossy-specific behaviour is not exercised and is defeated by highlights. |
| P2-5 (PL-0378) | **Resolved** | The designed missing sector `az05` is the only suggestion, with exact bounds 225–270 and a 45° gap. A contiguous gap 3–5 ranks its centre first. A test asserts that captured sectors are never suggested. A full orbit falls back to `full_rescan`. Reproducibility is asserted. All six mutants are killed. |

## Verdicts

| Task | Verdict | Basis |
|---|---|---|
| PL-0375 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | Criterion 1: the white HDPE matte renders (2 samples, σ 0 and 10) drive `low_object_surface_texture` and give overall `review_required` through the existing core QA and the Studio adapter. Criterion 2: the `claim_limit` fields hold, and no reconstruction or physical claim is made. Criterion 3: the input is deterministic, seeded, provenance-labelled synthetic data. P3-1..P3-4, P3-6 remain open. |
| PL-0376 | **CHANGES_REQUIRED** | P2-7. Provenance is fixed, but the glossy fixture does not exercise specular behaviour, and simulated specular highlights turn the gate into an all-pass `no_automated_concern`. |
| PL-0378 | **PASS (CLAUDE_PEER_AUDITED_PASS-eligible)** | Criteria 1–4 are met with discriminating tests: mutants M1–M6 are all killed, and determinism, the exclusion of occupied sectors and the `physical_orientation_claimed: false` flag are all asserted. P3-5 remains open. |

Hosted CI for `28c185e4` is green (run 42881593961). Physical, real-capture and factory gates remain open for all three tasks.
