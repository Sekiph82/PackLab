# Claude peer review — PL-0426 turntable angle sync prototype (V01)

Date: 2026-11-11. Reviewer: independent Claude reviewer (not the implementer).
Scope: commit `69b2e726` (`core/src/packlab_core/turntable_sync.py`, `tests/core/test_turntable_sync.py`, criteria `PL-0426_VALIDATION_CRITERIA_V01.md`, log `CLAUDE_IMPLEMENTATION_LOG_PL0426_V01.md`). Local `HEAD` = `origin/main` = `69b2e726a5183a41842900b5aadd055f5827d6f7`, clean tree.

## Verdict: CHANGES_REQUIRED

The core logic is sound and the virtual-camera math is correct for the convention the module uses. However, the module's output is not valid PackScan turntable metadata, and its angle sign convention is never tied to the frozen PackScan convention. Synchronizing angles into PackScan metadata is the task itself, so one P1 blocks `CLAUDE_PEER_AUDITED_PASS`.

## Evidence run

- `pytest tests/core/test_turntable_sync.py -q`: 11 passed.
- `ruff check core tests`: clean. `ruff format --check` on both files: clean.
- `mypy core apps tools`: no issues in 289 files.
- Hosted CI, read-only: "PackLab Windows Python Quality" run 42905352476 on head `69b2e726` finished SUCCESS. Signing Material Guard run 42905352394 also SUCCESS.
- Math check, 2000 random look-at poses with a seeded RNG (426). The object was rotated by `R_z(+θ)` about the station origin, then the fixed-camera coordinates were compared with the virtual-camera coordinates. Results:
  - Maximum residual: 4.5e-13 mm.
  - `RᵀR − I` and `det − 1`: at most 8.9e-16.
  - Composition `V(V(C,a),b) = V(C,(a+b) mod 360)`: 8.1e-13.
  - In PL-0397 station terms, turntable angle θ moves the virtual camera to station azimuth +θ (`camera_position` uses sin/cos from +y). For example, 30° gives 30.000° and 90° gives 90.000°.
  - Under the opposite (clockwise-object) reading, the same test gives a 49 mm error for a point at 50 mm radius and θ = 30°.
- PackScan QA: `_coverage_component` (`pre_reconstruction_qa.py:468-506`) accepts the emitted parameters (status `warning`, `manifest_records_one_turntable_frame_only`, as for any single turntable manifest).
- Schema check: `jsonschema` Draft 2020-12 against `schemas/packscan/manifest.schema.json` `$defs.turntable_mode` **rejects** the emitted parameters (see P1-1).
- Adversarial probes, all fail-closed or correct:
  - Tolerance edges: exactly 0.5 binds; 0.5000001 is unbound and reports its error.
  - Wrap-around: 359.8° and 0.3° bind.
  - Invalid inputs are rejected: bool, NaN, inf, str, `np.float32` NaN and `np.int64` sequence, negative sequence, list records, generator events, non-event objects, duplicate ids/sequences, more than 4096 photos or events, and NaN or non-16-element poses.
  - Events are frozen.
  - Output is identical under 20 random permutations of photos and events.
  - No aliasing between calls.
  - At the 4096 limit a call takes 0.84 s.
- Mutation testing on temp copies (22 mutants): 12 killed, 10 survived (see P2-3).
  - Killed: wrap removal, taking the first duplicate, ignoring the measured angle, rotation sign flip, orphan drop, 360 accepted, id-duplicate check, source regex, angle-source label swap, authority label, rotation-matrix translation, sort order.
  - Survived: `>=` at the tolerance edge, `frame_count` change, status ignoring orphans, tolerance upper bound removed, negative sequence allowed, max-events check removed, gap `or 360` removed, NaN check removed (equivalent: the range check still catches NaN), measured angle unvalidated, calibration label changed.

## Findings

### P1

**P1-1 — Emitted `capture_mode_parameters` are not valid PackScan turntable metadata, and the angle sign convention is not reconciled with the frozen contract.**
Files: `turntable_sync.py:141-145`, `172-188`; `schemas/packscan/manifest.schema.json:103-121`; `docs/packscan/manifest-contract.md:37-41`.

- The PackScan `turntable_mode.parameters` schema sets `additionalProperties: false`. It requires `angle_unit: "deg"` and `angle_convention: "clockwise_from_reference"` alongside `frame_index`, `frame_count` and `angle_deg`. The module emits only the last three, so validation fails with "'angle_unit' is a required property" and "'angle_convention' is a required property". With those two fields added, the parameters validate.
- Separately, the docstring says the object rotates "+angle about the station z axis". With +z up and a right-handed frame, that is counter-clockwise seen from above. The frozen PackScan convention is `clockwise_from_reference`.
  - The math happens to match one reading of that convention: virtual camera at station azimuth +θ, and PL-0397 azimuth is clockwise from +y seen from above.
  - It is inverted under the other reading, where the turntable/object turns clockwise, which would mirror reconstructed geometry.
  - Nothing in the code, tests or criteria states which reading applies, and the device events carry no direction convention.
- Validation criterion 1 ("produce the existing turntable `capture_mode.parameters`") is therefore not met as written. Criterion 4 ("correct") holds only under an undocumented convention.

Required:
- Emit `angle_unit` and `angle_convention`.
- Add a test that validates each emitted `capture_mode` against the manifest schema's `turntable_mode`.
- State the rotation sense explicitly (viewed from +z, object or camera azimuth) and its mapping to `clockwise_from_reference` and to the PL-0397 azimuth.
- Add a numerical test pinning that mapping, for example "turntable θ ⇒ virtual camera at `camera_position(azimuth=θ)`". If the intended reading is "object turns clockwise", flip the transform.

### P2

**P2-1 — `largest_angular_gap_deg` is wrong when two bound photos share an angle** (`turntable_sync.py:155-157`).
`... % 360.0 or 360.0` turns every zero gap into 360, not only the single-angle case. Angles {5, 5, 185} report 360.0; the correct value is 180.0. Restrict the 360 fallback to `len(angles) == 1`.

**P2-2 — Destination in PackScan metadata is undefined** (`turntable_sync.py:5-9`; log "Limits").
PackScan turntable `capture_mode` is manifest-level, and QA reports `manifest_records_one_turntable_frame_only`. Photo metadata (`photo-metadata.schema.json`, `additionalProperties: false`) has `photo_id` and `sequence` but no angle field. The module returns per-photo parameter dicts for a multi-photo set but never writes or validates any PackScan artifact. The log should state that this is a sync report only, and that writing into a manifest, one per frame, is still unbuilt. Otherwise "into PackScan metadata" is overstated.

**P2-3 — Test discrimination gaps.** Ten mutants survived (listed above). Most important:
- No test covers an invalid *measured* angle (NaN, or ≥ 360). If that validation regressed, a NaN measured angle would bind silently, because `nan > tol` is False. This is the fail-open path that matters.
- `status` ignoring orphans is not caught: the only orphan test also has unbound photos.
- Nothing pins `frame_count`/`frame_index` for an incomplete set.
- Nothing pins `physical_calibration_status`.
- Nothing covers the tolerance equality edge, a negative sequence, or the tolerance upper bound.

### P3

- `turntable_sync.py:104`: `record[0] in sequences.values()` makes the duplicate-id check O(n²) (0.84 s at 4096). Use a set.
- `turntable_sync.py:37`: `-0.0` is accepted and emitted as `-0.0`. Harmless, but normalise it with `+ 0.0`.
- `turntable_sync.py:172-194`: `virtual_camera_to_world` accepts non-rigid matrices (scale 2 passes). Its input frame must be the z-up PL-0397 station frame, but PackScan ARKit poses (`docs/packscan/pose.md`) are y-up and in metres. This is not guarded or documented at the call site. Nested 4x4 PackScan matrices are rejected, which is fail-closed and fine.
- `tests/core/test_turntable_sync.py:102-111`:
  - The comment places the camera "along -y", but PL-0397 defines +y toward the camera's initial position.
  - The identity rotation does not "look at the axis".
  - The orthonormality check covers row norms only, not orthogonality or the determinant.
- Contract "feature flag/fallback": the only fallback is that the library is not wired in. This is acceptable at prototype tier and consistent with the PL-0427 precedent, but the log should say so plainly.

## Contract / authority / safety

- Bounded: 4096 cap, tolerance limited to (0, 10]. Reproducible: pure, deterministic, permutation-invariant.
- Commercially licensable: stdlib only (`math`, `re`, `dataclasses`).
- No device control, Bluetooth, pairing or I/O. PL-0425 stays `BLOCKED_HARDWARE_TARGET_NOT_PRESENT`.
- The authority label `DEVICE_REPORTED_ANGLES_NOT_OBSERVED_GEOMETRY` and `PENDING_TURNTABLE_CALIBRATION` correctly disclaim physical and measurement authority. Scan Master and measurement authority are untouched.
- `matching.py` still refuses turntable input (`TurntableMatcherUnsupported`). This is consistent with architecture §10.
- The criteria faithfully cover "never invent", provenance, bounding and no-hardware. They miss the frozen PackScan schema and angle convention, a mandatory pre-read (`docs/packscan/manifest-contract.md`). That is the source of P1-1.

## Re-review condition

Fix P1-1 with schema-validation and convention tests, and fix P2-1 and P2-3 (at minimum: the measured-NaN test, status with orphans only, and frame_count on an incomplete set). Then this can become `CLAUDE_PEER_AUDITED_PASS` (prototype tier). Real turntable hardware and calibration remain pending.

Reviewer scratch (outside Git): `probe.py`, `math_probe.py`, `schema_probe.py`, `mutate.py` in the session scratchpad. No repository source, test, doc or TASKS.md edits, no commits or pushes.
