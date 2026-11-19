# PL-0401 scan-station repeatability across sessions

Status: software proxy implemented. Physical evidence is still **PHYSICAL_EVIDENCE_PENDING**.
No physical scan station exists yet. Seeded synthetic sessions only show that the software
math is correct. They are not a physical PASS.

Code:

- `core/src/packlab_core/station_session_repeatability.py`
- Tests: `tests/core/test_station_session_repeatability.py`
- Input: per reference object per session, one PL-0222 report from
  `repeat_scan_reproducibility.evaluate_repeat_scan_reproducibility`, plus the exact
  `RegistrationRevision` scans that the report was computed from. See
  `PL-0222_0223_REPRODUCIBILITY_AND_PRINT_SCALE_PROCEDURE.md`.

## Method

A session is one day or one setup. Each `StationSession` records station metadata:

- layout revision
- turntable driver identity
- lighting preset
- mat print record reference (the PL-0223 ruler record)
- pseudonymous operator reference
- UTC start time

### Common frame (precondition for pooling sessions)

PL-0222 reports its axis extents in the frame of its own reference scan. An object re-placed on
another day would therefore show a dimension change even when nothing changed: the V01 review
measured a false drift at a 1° yaw. Before any statistics are computed, the module does three
things:

1. **Binds the supplied scans to the report.** It checks that:
   - the revision IDs match the report's scans exactly;
   - the parent digest, scale provenance, project and coordinate unit match;
   - the report's own extents are reproduced from the scan points and the report's transforms.

   Any mismatch fails closed.
2. **Registers each session's reference scan rigidly to one canonical reference per object.**
   The canonical reference is the reference scan of the chronologically first session. The
   registration uses the accepted `register_repeat_scans` and never scales.
3. **Recomputes every used scan's extents** as axis-aligned extents in the canonical frame.

If the registration is not accepted, the run fails closed with
`cross_session_reference_registration_not_accepted`. This happens for a wrong object, a partial
capture, or a large re-placement without a coarse alignment. The registration is never skipped.

For large re-placements, give an operator coarse alignment with
`initial_transforms[(session_id, object_id)]`. For example, a 90° turn of a 100 x 60 mm box is
refused without one and accepted with one.

Every `initial_transforms` key must be a `(session_id, object_id)` pair that is actually
registered in the run. The first session is the canonical frame, so it can never take a key.
Unknown, misspelled or unused keys fail closed with `initial_transform_key_unknown_or_unused`.

Each session's `reference_alignment` record holds:

- the registration ID, inlier ratio and RMSE
- `initial_transform_supplied` and the `initial_transform` that was used (identity if none)
- the final transform
- `rotation_to_canonical_deg` (total re-placement rotation)
- `rotation_beyond_initial_deg` (what ICP changed beyond the seed)

The report also records `registration_adapter`, the module and class of the geometry adapter.

Registration error goes into the between-session component. A small rotation error changes
axis-aligned extents to first order. On real data this registration error is **unmeasured**:
the synthetic clouds share sample positions, while real scans do not and will register worse.
The ICP acceptance gate does not bound the residual rotation tightly, so the reported `s_L`
(and every drift flag) is **biased upward by alignment error** relative to true station drift (on average; a single ANOVA estimate also has sampling error and is truncated at zero). It mixes station drift
with alignment error and cannot separate them.

### Statistics

Per object and axis, the module runs a one-way random-effects ANOVA with sessions as groups.
This follows ISO 5725-2, and unbalanced designs are allowed:

- `s_r^2 = MSW` (repeatability)
- `s_L^2 = max(0, (MSB - MSW) / n0)` (between-session)
- `s_R^2 = s_r^2 + s_L^2` (reproducibility)

Scans that PL-0222 flagged are not used. These are partial coverage, scale outliers and
rejected registrations.

The module flags two kinds of session:

- **`session_mean_drift`**: the shift of the session mean from the leave-one-out mean of the
  other sessions exceeds both:
  - `drift_k_standard_errors` (default 5) times the SE;
  - `minimum_drift_shift` (default 0.05 in the coordinate unit).

  The SE is `sqrt(s_L,other^2 + s_r,other^2/n_i + MSB_other/N_other)`. The practical floor
  keeps noise-free input well defined: when SE = 0, only a shift above the floor is flagged,
  and `k_standard_errors` is null.
- **`station_configuration_change:<field>`**: the layout, turntable, lighting or mat record
  differs from the previous session in time order. A change of operator alone is not flagged,
  because operator variation is part of reproducibility.

Any flag, and any worst-case `s_r` or `s_R` above its threshold, gives
`EXCEEDS_PROVISIONAL_THRESHOLDS`.

### Fail-closed conditions

The run raises when any of these hold:

- fewer than `minimum_sessions` sessions (default 5, never fewer than 3)
- fewer than `minimum_repeats_per_session` used scans (default 2)
- object ID sets, or report and scan sets, differ between sessions
- an object ID or session ID is not a pseudonymous string `[A-Za-z0-9][A-Za-z0-9._:-]{0,63}`
- an object's project ID changes between sessions
- the cross-session reference registration is not accepted
- an object's session mean extent is more than 5 % from the median (a different object)
- a PL-0222 digest is invalid, or its contract is unsupported
- a PL-0222 report is not `simulation_only` or not PENDING
- scale state, unit or claimed evidence class is mixed between reports
- the scale state is not METRIC_UNVERIFIED (`scale_state_must_be_metric_unverified`)
- a report is reused
- a scan revision ID or scale provenance is shared between reports
- the scans do not reproduce the report
- extents or transforms are invalid
- session IDs or timestamps are duplicated
- a timestamp is not UTC
- a metadata reference is unsafe or empty
- the thresholds or policy are untyped

The report is versioned (`packlab.station-session-repeatability-report.v1`) and digest-bound.
Check it with `report_digest_valid`. The report always has:

- `simulation_only: true`
- `physical_validation_status: PHYSICAL_EVIDENCE_PENDING`
- `physical_repeatability_claim: false`

The thresholds `status` is fixed to `PROVISIONAL_PENDING_PL-0221` (`init=False`). Callers
cannot relabel it.

## Drift-test tuning (in-sample, synthetic, one configuration)

The defaults k = 5, `minimum_sessions` = 5 and `minimum_drift_shift` = 0.05 were chosen
**in-sample** on a single synthetic configuration. These rates do NOT predict physical
false-alarm rates.

The configuration:

- 2 box objects, 100 x 60 x 40 and 30 x 30 x 18
- 4 repeats per session
- Gaussian `s_r` = 0.02 and `s_L` = 0.01, so `s_L / (s_r / sqrt(n))` is about 1
- POLICY from the PL-0222 tests

Over seeds 0–299 (`_sessions(seed=s, count=n)`):

| Sessions | Evaluations with any false drift flag | Exact detection |
| --- | --- | --- |
| 5 | 0.7 % | 83 % |
| 6 | 1.0 % | 84 % |
| 12 | 0.7 % | 91 % |

"Exact detection" means a +0.1 x-extent shift injected on `pp-cap-proxy` in session `s2`
(`shift=(2, "pp-cap-proxy", 0.1)`) is flagged on exactly that session. The seeded test fixture
(`test_injected_drifted_session_is_flagged`) checks a 0.4 shift on one seed.

With few sessions, the estimated between-session variance has heavy tails. Re-measure before
you change `minimum_sessions`, k or the floor.

To reproduce (takes about 3 minutes):

```
.venv/Scripts/python.exe -c "import sys; sys.path[:0]=['core/src','.']; from tests.core.test_station_session_repeatability import drift_rates; print(drift_rates())"
```

## Operator procedure (once a physical station exists)

1. Pick two or more reference objects with stable dimensions. Use matte HDPE and PP
   benchmark parts from PL-0220. Do not use factory samples until the Kenya gate opens.
   Prefer objects without rotational symmetry in the image plane, or mark a fixed placement
   orientation on the mat.
2. Hold at least 5 sessions on different days or setups.
   - In each session, scan every object at least 2 times. This is the code default
     `minimum_repeats_per_session`; 3 or more is recommended. If you require 3, set the
     threshold to 3.
   - Re-place the object between scans in roughly the same orientation.
3. At the start of each session, record the station metadata. Use pseudonymous operator and
   object IDs only, with no names or e-mails. The mat print record must refer to that day's
   PL-0223 ruler record.
4. Run PL-0222 for each object in each session. Keep every report and its exact
   `RegistrationRevision` inputs unmodified.
5. Run `evaluate_station_session_repeatability(sessions, policy=...)`. If an object was
   re-placed by more than a few degrees and the run refuses, give a coarse
   `initial_transforms` entry for that session and object. Archive the report together with
   its `report_sha256`.
6. Investigate every `session_mean_drift` or `station_configuration_change` flag before you
   pool results. Restart the series after any intended layout, mat or lighting change.
7. A physical PASS needs all of the following, and this software cannot supply any of them:
   - real scans
   - owner-verified scale records (METRIC_VERIFIED binding is not possible in v1)
   - thresholds accepted under PL-0221
   - an independent review

## Limits

- Only overall axis extents are decomposed. They are axis-aligned in the canonical frame, so
  they depend on the canonical reference's pose, but that dependence is the same in every
  session. PL-0222 publishes surface residuals pooled per report, not per scan, so no surface
  decomposition is done.
- Symmetric objects can register to a symmetric pose. Axis-aligned extents are unaffected
  only when the symmetry maps the bounding box onto itself.
- PL-0222 digests are unkeyed SHA-256. They detect accidental edits, not forgery.
- The drift SE uses `MSB/N` for the variance of the other sessions' grand mean, which is exact
  only for balanced designs. The k threshold uses a normal-style rule, not Student-t quantiles.
- Drifted sessions remain in the variance decomposition. They are flagged, not removed.
