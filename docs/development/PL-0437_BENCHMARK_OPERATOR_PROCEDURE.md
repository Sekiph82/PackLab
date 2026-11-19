# PL-0437 reconstruction backend benchmark: operator procedure

Status: software harness implemented. Physical evidence is still **PHYSICAL_EVIDENCE_PENDING**.
No physical benchmark objects, caliper record or real backend runs exist yet. The seeded
synthetic proxy only shows that the comparison maths and fail-closed gates work. It is not
evidence that either backend is accurate.

Spec: `docs/implementation/PL-0437_RECONSTRUCTION_BACKEND_BENCHMARK.md`.

Code:

- `core/src/packlab_core/backend_benchmark.py`
- Tests: `tests/core/test_backend_benchmark.py`
- Physical ground truth: `core/src/packlab_core/physical_accuracy_benchmark.py`
  (`PhysicalAccuracyBenchmarkRecord`, serialized with `serialize_physical_benchmark_record`).

## What the harness does and does not do

- It compares run records that already exist. It does not run COLMAP, OpenMVS or VGGT.
- It **never** changes the production default. Every report has
  `production_default_backend = "colmap-openmvs"` and `production_default_changed = false`.
- The best result it can give is `RECOMMEND_DEFAULT_CHANGE_PENDING_ADR`. That result is only a
  recommendation. Before any default changes you still need a licence clearance review, an
  explicit ADR, a Scan Master authority regression review and an independent reviewer. The report
  lists these follow-ups as reminder strings. They are not evidence.

## Trust boundary: what is attested and what is verified

- **Physical binding is owner-attested, not cryptographically authenticated.** The physical
  record digest is an unkeyed sha256, so anyone can recompute it. If invented caliper values are
  relabelled as `PHYSICAL_CALIPER` and given new names and identities, this harness cannot detect
  it. The test helper `_relabel_as_physical` does exactly that, on purpose, so the decision logic
  can be tested. An independent reviewer must check every bound case against the real record,
  samples and captures before the report is accepted.
- The harness does refuse the obvious relabels:
  - `SYNTHETIC_GENERATOR` and `PUBLIC_PROXY` authorities;
  - identifiers containing a `syn`, `synthetic` or `proxy` segment (case, capture set, ground
    truth, sample or record id) on the physical path;
  - the synthetic proxy backend identities (version `synthetic-proxy`, licence `proxy-license`,
    or a `syn`/`synthetic`/`proxy` segment in the version, build or licence). Do not use those
    words in real identifiers.
- **"Pinned" means declared.** A backend counts as pinned when it has exactly one identity
  across all runs and declares sha256-shaped `executable_hashes`. Nothing checks those hashes
  against the binaries or checkpoint. The reviewer must do that.
- **`license_clearance_ref` is an owner-attested token.** It is not compared with the backend's
  `license_record`. It only records which licence review the owner cites.

## Decision outputs

| Decision | When |
| --- | --- |
| `NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE` | Any case is not physically bound (see the trust boundary above). Or a required class has fewer independent objects than the minimum. Or a backend has too few repeats on a case, or the baseline failed a run or missed a quality band on a case. |
| `NO_CHANGE_RULE_NOT_MET` | The physical evidence is complete but one of these holds: the rule fails, a deciding metric is missing, a candidate run failed or missed a quality band, a backend identity is unpinned or is the synthetic proxy, or no licence clearance reference was recorded. |
| `RECOMMEND_DEFAULT_CHANGE_PENDING_ADR` | All of the above pass. |

Synthetic or public-proxy ground truth always gives `NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE`.

## Pre-registered decision rule (`pl0437-equal-or-better-v1`)

`DecisionRule()` defaults. The report records the rule and its `rule_digest`. Decide the rule
before you look at any results.

- **Classes:** `matte_bottle`, `glossy_bottle`, `jerrycan` (the PL-0221 categories).
- **Minimum evidence:** at least 3 **independent physical objects** per class and at least
  2 repeats per backend per case.
  - Every case needs its own `capture_set_id`. A capture set reused across cases is rejected.
  - A physical sample is not the same thing as a physical object. The PL-0221 record holds one
    caliper dimension per sample, so one bottle can appear as several samples. The harness
    derives an object key from the record: samples that share a `scan_id` or `measurement_id`
    are merged into one object.
  - Cases that resolve to the same object (for example orbit and turntable captures, or the
    height, width and depth samples of one bottle) are averaged into one value before the
    statistics, so they cannot inflate *n*. The report shows each case's `physical_object_key`
    and each class's `independent_objects`.
  - **Owner requirement:** every counted case must come from exactly one physical object, and
    every sample of that object must share its `scan_id` or `measurement_id`. Two different
    objects must never share either id. The harness cannot tell when one object is recorded
    under unrelated scan and measurement ids, so the reviewer checks this.
- **Quality bands (per run):** `surface_coverage_ratio >= 0.90` and
  `registered_input_ratio >= 0.80`, checked with `benchmark_metrics.compare_metric_bands`. They
  apply to both backends.
  - A candidate run that misses a band fails the rule.
  - A baseline run that misses a band makes that case not comparable, because a degenerate
    baseline would flatter the candidate.
- **Deciding metrics:** computed per case and backend over the repeats.
  - `dimension_mae_mm`: mean absolute error across the ground-truth dimensions.
  - `scale_error_ratio`: `|median(measured/truth) - 1|`.
  - `surface_coverage_loss`: `1 - coverage`.
  - `repeatability_spread_mm`: the largest max-min spread of any dimension.
  - `surface_deviation_rms_mm`.
  - `operator_interventions`.

  Every one of them is required. If either backend leaves one out on any case, that class gets
  `NOT_MEASURED`, which fails the rule.
- **Statistic:** the paired delta is candidate minus baseline, where positive means the
  candidate is worse. Average the delta per object, then take the one-sided 95% Student-t upper
  confidence bound of the mean over the objects.
- **Pass condition (equal or better):** for every class and metric, the upper bound must be
  **≤ 0**, because every default margin is 0. This is the conservative reading of the spec's
  "equal or better". If the candidate's deltas vary at all, being statistically
  indistinguishable from the baseline does **not** pass: the candidate must show it is at least
  as good with 95% confidence. One edge case does pass. A candidate whose results are
  bit-identical to the baseline has zero variance and a mean of 0, so its upper bound is
  exactly 0 and it reaches `RECOMMEND_DEFAULT_CHANGE_PENDING_ADR`. That is consistent with
  "equal".
- **Margins option:** `DecisionRule` lets you set positive per-metric margins, which turns the
  rule into a non-inferiority test. That is a different interpretation of the spec. It needs
  explicit owner/ADR sign-off and a new rule `version` recorded before the data is seen.
- **Any failed candidate run** fails the rule.
- **Descriptive only:** the report's per-case `descriptive` block holds registration ratio,
  runtime, peak RAM, VRAM, point and triangle counts, holes, floating components, interventions
  and failure diagnostics. These values never decide, because the spec says not to select a
  backend because it is faster.

With only 3 objects per class the t quantile is 2.92, which is strict. Plan 5 to 10 independent
objects per class.

## Owner procedure with real objects

1. **Objects.** Use owner-approved or public objects only: at least three independent objects for
   each class (matte bottle, glossy/reflective bottle, and jerrycan or handled asymmetric
   package). Do not commit confidential Kenya supplier scans or images to this public repository.
2. **Ground truth.** Measure each object with a calibrated caliper using the M09/M17 procedure.
   Record the result as a `PhysicalAccuracyBenchmarkRecord` with status `READY_FOR_AUDIT`,
   `ACCEPTED` samples and full environment metadata. Serialize it with
   `serialize_physical_benchmark_record` and keep the file outside Git.
3. **Captures.** Take a separate PackScan capture set for each case. Both backends must use the
   same capture set. Keep guided-orbit and turntable sets as separate cases.
4. **Pin backends.** Record each backend's `BackendProvenance`, including the
   `executable_hashes` of the COLMAP/OpenMVS binaries and the VGGT commercial checkpoint SHA from
   an activated `VGGTReconstructionBackend.provenance()`. Use one build per backend for the whole
   benchmark. An unconfigured VGGT provenance has no hashes and blocks any recommendation.
5. **Run.** Run each backend at least twice per case. Measure every output with the **same** M09
   scale procedure (one `scale_procedure_id`) and record the six dimensions. `body_diameter` is
   optional. Report `surface_deviation_rms_mm` for every run against a reference surface. A run's
   `scale_state` must stay `relative` or `metric-unverified`. The harness rejects
   `metric-verified`, because M09 and Scan Master own that state. Record failed runs as `FAILED`
   with a diagnostic. Do not drop them.
6. **Input file.** Write the input JSON (contract
   `packlab.reconstruction-backend-benchmark-input.v1`, at most 16 MiB) outside Git. Every field
   below must hold a real value. The `<...>` placeholders are not valid input.

   ```json
   {
     "contract": "packlab.reconstruction-backend-benchmark-input.v1",
     "license_clearance_ref": "<licence review reference>",
     "backends": {
       "baseline": {"backend_id": "colmap-openmvs", "version": "<v>", "build": "<b>",
                    "license_record": "<l>", "executable_hashes": {"colmap": "<sha256>"}},
       "candidate": {"backend_id": "neural-experimental", "version": "<v>", "build": "<b>",
                     "license_record": "<l>", "executable_hashes": {"checkpoint": "<sha256>"}}
     },
     "cases": [{"case_id": "<id>", "package_class": "matte_bottle", "material": "hdpe_matte",
                "capture_set_id": "<unique id>", "ground_truth_record_id": "<caliper ground_truth_id>",
                "ground_truth_authority": "PHYSICAL_CALIPER",
                "ground_truth_dimensions_mm": {"height": "<mm>", "max_width": "<mm>",
                  "max_depth": "<mm>", "neck_finish_diameter": "<mm>",
                  "base_diameter_or_footprint": "<mm>"},
                "physical_record_digest": "sha256:<64 hex>", "physical_sample_id": "SAMPLE-<id>"}],
     "runs": [{"case_id": "<id>", "backend": "baseline", "repeat_index": 0,
               "status": "SUCCEEDED", "scale_procedure_id": "<m09 procedure id>",
               "scale_state": "metric-unverified", "measured_dimensions_mm": {"height": "<mm>"},
               "surface_coverage_ratio": "<0..1>", "registered_input_ratio": "<0..1>",
               "surface_deviation_rms_mm": "<mm>", "runtime_seconds": "<s>",
               "peak_host_ram_bytes": "<int>", "operator_interventions": 0}]
   }
   ```

   A case is physically bound only when all of these hold:
   - the record is `READY_FOR_AUDIT` and its digest matches the case;
   - no identifier looks synthetic;
   - the sample is `ACCEPTED` and in the same class;
   - `ground_truth_record_id` is the sample's caliper `ground_truth_id`;
   - the caliper `value_mm` equals the case's value for that dimension.
7. **Evaluate.**

   ```
   .venv/Scripts/python.exe -m packlab_core.backend_benchmark --input <input.json> \
       --physical-record <physical-record.json> --out <report.json>
   ```

   For a software dry run with no real data, use `--synthetic-proxy`. It always gives
   `NO_CHANGE_INSUFFICIENT_PHYSICAL_EVIDENCE`.
8. **Archive and review.** Keep the input, the physical record and the report outside Git. Cite
   `report_digest`, `rule_digest`, `manifest_digest`, `runs_digest` and the physical
   `record_digest` in the review record. Any default change needs a separate ADR and review.

## Reviewer checklist (attested items the harness cannot verify)

- [ ] Every bound case's caliper sample, scan and capture set exist in the real evidence and
      match the record.
- [ ] **One physical object per counted case.** Each `physical_object_key` in the report is
      exactly one real object. Samples of the same object share a `scan_id` or
      `measurement_id`, and different objects never share either. `independent_objects` per
      class equals the real count of distinct objects.
- [ ] The declared `executable_hashes` match the actual COLMAP/OpenMVS binaries and the VGGT
      commercial checkpoint.
- [ ] `license_clearance_ref` points to a real, completed licence review for the candidate.
- [ ] The rule `version` and `rule_digest` were fixed before the data was collected.

## Limits

- The PL-0221 physical record has one caliper dimension per sample. That one dimension is
  checked against the record. The other ground-truth dimensions are bound only through
  `manifest_digest`.
- `surface_deviation_rms_mm` needs a reference surface, such as a CT or structured-light mesh.
  The harness does not compute it from meshes. It only compares values that you supply.
- The quality floors (0.90 coverage, 0.80 registration) are pre-registered engineering choices,
  not measured process limits. Confirm them before the first real benchmark.
- The synthetic-identifier guard works on names. It catches accidental mix-ups, not deliberate
  forgery.
- The golden proxy report digest changes whenever the report format changes. The current value
  was checked only on Windows (Python 3.12). Earlier revisions matched on Linux. It has not
  been checked on macOS.
- Object identity is derived from shared `scan_id` or `measurement_id`. An object recorded
  under unrelated ids is counted twice. The reviewer checklist covers this.
