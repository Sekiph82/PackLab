# Claude peer review — PL-0426 turntable angle sync, V02 re-review

Date: 2026-11-11. Reviewer: independent Claude reviewer (not the implementer, not the V01 reviewer's code).
Scope: fix commit `f8a8a48b7647b7c06813b34b48b01fc0b1a29caf` responding to `CLAUDE_PEER_REVIEW_PL0426_V01.md`.
Files: `core/src/packlab_core/turntable_sync.py`, `tests/core/test_turntable_sync.py`, `docs/packscan/manifest-contract.md`, the updated implementation log and `PL-0426_VALIDATION_CRITERIA_V01.md`.
These three files are unchanged between `f8a8a48b` and the current `HEAD`. A later `label-artwork` commit on `main` is out of scope.

## Verdict: PASS — eligible for `CLAUDE_PEER_AUDITED_PASS` (prototype tier)

P1-1, P2-1, P2-2 and the minimum P2-3 items from V01 are resolved with evidence. No P0, P1 or P2 findings remain; the P3 items below are non-blocking.

Still pending and outside this verdict:
- real turntable hardware and physical calibration;
- PL-0425 (`BLOCKED_HARDWARE_TARGET_NOT_PRESENT`);
- wiring into the matcher/reconstruction (`TurntableMatcherUnsupported` is unchanged).

Hosted CI for `f8a8a48b` was still running when this review was written (see Evidence). Record the CI conclusion together with the acceptance.

## 1. Convention: "clockwise seen from above"

Where angles appear in the repo:
- **Schema:** `schemas/packscan/manifest.schema.json:116` fixes only the token `clockwise_from_reference`, with no viewpoint.
- **Producers:** none emit turntable `angle_deg` with a direction.
  - iOS `TurntableCoverageModel` (`apps/ios-capture/PackLabCapture/Services/M04CaptureEngine.swift:1256-1275`) only normalizes angles into sectors.
  - The manual "Angle degrees" field (`ContentView.swift:716`) has no stated direction.
  - The iOS app does not emit the `clockwise_from_reference` parameters.
- **Consumers:** none are direction-sensitive.
  - `pre_reconstruction_qa.py:468-502` checks range and frame index only.
  - The fixtures (`manifest-valid-turntable.json`, `manifest-invalid-turntable-guided.json`) carry no direction.
- **Station frame:** PL-0397 / `scan_station_layout.py:3,73-77` defines azimuth as clockwise from +y seen from above (`+Y_TO_PLUS_X`, `blender_label_render_overlay.py:386`).

Judgement:
- A turntable angle naturally describes the platter's rotation. Turntables and motors state CW/CCW looking down at the platter. So "the platter turns clockwise as seen from above" is the natural reading, and it is consistent with the station frame's clockwise-from-above azimuth.
- **Doc change:** clarifying `docs/packscan/manifest-contract.md:40-42` without a version bump is acceptable. The schema is unchanged and the constant is unchanged. The change only resolves an under-specified viewpoint that no artifact, producer or consumer depended on, so no existing data can be reinterpreted. A versioned schema change would be needed only if an existing producer had been emitting the opposite sense; none exists.
- **Traceability:** see P3-5.

## 2. Transform direction: independent numerical check

Script: `scratchpad/pl0426_v02/probe.py`, outside Git, seed 4262.

Platter rotation:
- I independently modelled clockwise-from-above platter rotation as object points mapped by `R_z(-θ)`. `R_z(-90°)` maps +x to −y, which is clockwise looking down −z.
- Over 2000 random look-at cameras (z-up station frame, mm), I compared the fixed camera's view of the rotated object point, `C⁻¹·R_z(-θ)·p`, against the virtual camera's view of the unrotated point, `V(C,θ)⁻¹·p`.
  - Maximum residual: **6.8e-13 mm**.
  - Under the opposite (counter-clockwise) reading, the error is 46.4 mm for a 50 mm-radius point at 30°.

Matrix properties of the output:
- Orthonormality `|RᵀR−I|` ≤ 6.7e-16, and `|det−1|` ≤ 8.9e-16.
- Composition `V(V(C,a),b) = V(C,(a+b) mod 360)` holds to 1.7e-12.

PL-0397 azimuth mapping:
- A camera at station azimuth `a` maps to virtual azimuth `a − θ`. Checked cases: (0,30)→330, (0,90)→270, (45,100)→305, (300,350)→310, all exact.

Rigidity guard:
- Diagonal perturbation 1e-7 is accepted; 5e-7 and above give `camera_to_world_not_rigid`.
- Bottom rows `[0,0,0,2]` and `[0,0,0.001,1]` are rejected.
- A float32-rounded look-at pose is accepted.
- **A reflection (det −1) is accepted** (P3-1).
- Angles NaN, 360, −1e-9 and `True` are rejected.

## 3. Schema validation of emitted parameters

Method:
- 300 random sessions with a seeded RNG, 1–40 photos each.
- About 15% missing events, duplicate events, orphan events, measured/commanded mixes, ±1° measurement noise, and angles at −0.0 and 359.9999999.
- Each bound photo's parameters were inserted into the real `manifest-valid-turntable.json` fixture. The **full manifest** was then validated with `Draft202012Validator` plus the format checker.

Results:
- **3196/3196 valid**, including INCOMPLETE sets.
- `0 ≤ frame_index < frame_count` holds in every case.
- Output was identical when photo and event order were reversed.

Gap and performance:
- Gap probes: {5,5,185} gives 180 (P2-1 fixed); {5} and {5,5} give 360; {350,10} gives 340; no bound photos gives None.
- 4096 photos and events run in 0.005 s (V01 measured 0.84 s, so P3 O(n²) is fixed). 4097 photos raises `photos_invalid`.

## 4. Mutation testing (temp copies; the repo test file was pointed at the repo schema path)

Script: `scratchpad/pl0426_v02/mutate.py`. The unmutated baseline passes.

**V01 mutant set (22): 19 killed, 3 survived.**

Seven of V01's ten survivors are now killed:
- `>=` at the tolerance edge;
- `frame_count` change;
- status ignoring orphans;
- tolerance upper bound removed;
- negative sequence allowed;
- measured angle unvalidated (the fail-open path V01 flagged);
- calibration label changed.

The three that still survive:
- `no_nan_check`: equivalent mutant, because the range check rejects NaN.
- `gap_old_or360`: now equivalent, because distinct sorted angles never produce a zero gap.
- `no_max_events`: not tested (P3-4).

**V02-specific mutants (13): 8 killed, 5 survived.**

Killed:
- `angle_unit` removed;
- `angle_convention` removed;
- wrong convention string;
- gap list instead of set;
- whole rigidity check removed;
- loose rigidity tolerance;
- `frame_index` offset;
- transposed rotation application.

Survived (all P3):
- single-angle gap set to 0;
- −0.0 normalisation removed;
- diagonal-only rigidity check;
- off-diagonal-only rigidity check;
- bottom-row check removed.

The rotation-sign flip (`rot_sign`) is killed by the direction pin at `test_turntable_sync.py:105`.

## Evidence run

- `pytest tests/core/test_turntable_sync.py tests/core/test_pre_reconstruction_qa.py -q`: **26 passed**.
- `ruff check core tests`: all checks passed. `ruff format --check` on both changed Python files: already formatted.
- `mypy core apps tools`: no issues in 289 source files.
- `jsonschema>=4.0,<5` is a declared dependency (`pyproject.toml:19`), so the new schema test can run in CI.
- Hosted CI (`gh run list --branch main --limit 4`, read-only) for head `f8a8a48b`:
  - Signing Material Guard 42906973852: **success**.
  - Windows Python Quality 42906974101: **cancelled**. It was superseded by a newer push to `main`.
    - The superseding run 42907481785 is on head `1bbfe32f`, which descends from `f8a8a48b` (checked with `git merge-base --is-ancestor`). It was **in_progress** at the end of this review.
  - Capture macOS CI 42906973924: **in_progress** when last checked.
  - V01 head `69b2e726` Windows Python Quality 42905352476 was SUCCESS.
  - The accepting agent must record the conclusion of run 42907481785 (or a later run whose head contains `f8a8a48b`) before marking the task `[x]`.

## V01 findings disposition

| V01 | Status | Evidence |
|---|---|---|
| P1-1 schema fields | Fixed | `turntable_sync.py:149-150`; full-manifest validation 3196/3196; test `:123-145` |
| P1-1 rotation sense | Fixed | Docstrings `:10-11`, `:191-195`; contract doc; independent derivation residual 6.8e-13 mm; direction pin `:105` |
| P2-1 gap | Fixed | `:160-171`; {5,5,185} → 180 |
| P2-2 overclaim | Fixed | Module docstring `:13-14` and log V02 §P2-2 now say "sync report; caller writes manifest" |
| P2-3 tests | Fixed (required minimum met) | Measured NaN/360/−1/bool, orphan-only INCOMPLETE, incomplete-set indices/count/calibration label, tolerance edge, negative sequence, tolerance upper bound |
| P3 O(n²), −0.0, non-rigid, z-up note | Fixed | Exceptions: reflections (P3-1) and an ineffective −0.0 test (P3-2) |

## Findings

### P0 / P1 / P2

None.

### P3 (non-blocking)

**P3-1 — Reflections pass the rigidity guard** (`core/src/packlab_core/turntable_sync.py:205-212`).
- `diag(1,1,−1)` is orthonormal but improper (det −1), so it is accepted under the `camera_to_world_not_rigid` contract and produces a mirrored pose.
- Fix: add a `det(R) > 0` check, or a cross-product check `row0 × row1 ≈ row2`.

**P3-2 — The −0.0 normalisation test cannot fail** (`tests/core/test_turntable_sync.py:187`).
- `-0.0 == 0.0` is True, so removing `+ 0.0` (`turntable_sync.py:44`) survives.
- Fix: assert `math.copysign(1.0, value) == 1.0`, or check the JSON/repr output.

**P3-3 — Test comments.**
- `test_turntable_sync.py:107-109` describes a "direction pin" with a platter point, but the code that follows checks only orthonormality. The actual pin is line 105.
- The camera at −y (`:103`) still contradicts PL-0397's "+y toward the camera" (V01 P3, carried over). The math is unaffected.

**P3-4 — Remaining non-equivalent survivors.**
- These are the 4096 cap, single-angle gap = 360, the bottom-row check and the two halves of the rigidity check (each half alone kills the single shear case).
- The schema test (`:146`) validates only a complete orbit; this review's probe covered incomplete sets.

**P3-5 — Traceability of the frozen-contract clarification** (`docs/packscan/manifest-contract.md:40-42`).
- Add a one-line note: "clarified under PL-0426, 2026-11-11; schema unchanged; no prior producer encoded a direction". This keeps the PL-0052 frozen-contract audit trail honest.
- Also state the PL-0397 mapping (virtual camera azimuth = `a − θ`) in the `virtual_camera_to_world` docstring, as V01 asked. The direction itself is already unambiguous and pinned.
- When iOS manual or turntable angle entry (`ContentView.swift:716`) is wired to PackScan, it must show operators the clockwise-from-above convention.

**P3-6 — Cosmetic.**
- `turntable_sync.py:215` rebuilds `m`, duplicating `m0` (`:203`).
- `np.float32` elements are rejected as `camera_to_world_invalid`. This is fail-closed, but a caller must convert to Python floats first.

## Contract / authority / safety

- Still pure stdlib, with no I/O, device control, Bluetooth or pairing.
- Bounded at 4096 photos/events with tolerance in (0, 10]. Deterministic and order-invariant.
- Authority labels are unchanged: `DEVICE_REPORTED_ANGLES_NOT_OBSERVED_GEOMETRY` and `PENDING_TURNTABLE_CALIBRATION`. No Scan Master or measurement authority claim.
- The fallback (nothing calls the library, so the manual and guided-orbit workflows are the default) is stated plainly in the log.
- No synthetic-as-real claims. Events are labelled `SYNTHETIC-*`.

Reviewer actions: read-only. Probes and mutants ran in the session scratchpad (`pl0426_v02/`), outside Git. The only file written to the repository is this review, uncommitted. No source, test, doc or TASKS.md edits, commits, pushes, stashes or branch changes.
