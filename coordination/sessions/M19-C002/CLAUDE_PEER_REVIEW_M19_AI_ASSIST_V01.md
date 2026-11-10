# Claude Peer Review: M19 AI-Assist Batch (PL-0420 to PL-0424), V01

Date: 2026-11-10
Reviewer: independent Claude peer reviewer. I did not write the code under review. Codex wrote it, and it was published in `260beb49`.
Mode: read-only review. I made no edits to source, tests, docs or `TASKS.md`, and I made no commit or push. All mutation experiments ran on temporary copies under the session scratchpad, and those copies were deleted afterwards.

## Scope and SHAs

- Code published in `260beb49` (2026-11-10 18:45). Mypy-only Optional narrowing was applied in `0176a67e`. I diffed that commit: it changes `utcoffset()` in 3 modules and does not change behaviour.
- HEAD at the start of the review was `0e9549bd`. HEAD at the end was `e95879ea`, because other agents committed in the meantime. `git diff HEAD` shows the reviewed files are identical at both.
- Files reviewed:
  - `docs/implementation/PL-0420_LEARNED_FEATURE_RECOGNITION_RESEARCH.md`
  - `core/src/packlab_core/{package_family_suggestion,profile_zone_proposal,dimension_fit_proposal,reconstruction_anomaly}.py` and the matching `tests/core/test_*.py`
  - The M19-C002..C006 PROMPT, VALIDATION_CRITERIA and CODEX_LOG files
  - The mandated dependencies: `packaging_asset.py`, `design_profile_zones.override_design_profile_zones`, `geometry_statistics.py`, `reconstruction_confidence.py`
- `TASKS.md`: PL-0420..0424 are all `[ ]`, with the generic Claude execution contract ("Prototype a bounded, reproducible, commercially licensable solution with feature flag/fallback, measurable tests and reviewer evidence ..."). At `260beb49`, duplicate historical `[x]` lines existed. They were withdrawn in `d1f3e952`.

## Commands and results

| Command | Result |
| --- | --- |
| `QT_QPA_PLATFORM=offscreen PYTHONPATH=core/src .venv/Scripts/python.exe -B -m pytest -q` on the 4 target test files plus `test_design_profile_zones`, `test_design_history`, `test_geometry_statistics` and `test_packaging_asset` | **73 passed** |
| `ruff check core apps tools tests` | All checks passed |
| `ruff format --check --config "format.line-ending = 'auto'"` on the 8 target files (the CI form) | 8 files already formatted. Without that config, the CRLF working copy reports "would reformat", which is a line-ending artifact only. |
| `mypy core apps tools` | Success, no issues in 288 source files |
| `gh run list --branch main` (read-only) | Windows Python Quality `42882742666` (08ed55e2) passed: 2652 passed, 16 skipped. Signing guard green. Run `42885936327` (727bedbf) was still in progress when I checked. `pyproject` `testpaths=["tests"]`, so the CI run includes these 4 modules. |
| Adversarial probe script (scratchpad `probe_m19.py`) | Results are in the findings below |
| Mutation script (scratchpad `mutate_m19.py`, run on a temp copy with mirrored `core/src` + `schemas` + `tests/core`) | 16 mutants: **8 killed, 8 survived** |

### Codex log claims checked against reality

- Test counts match exactly: 5 (PL-0421), 5 (PL-0422), 4 (PL-0423), 4 (PL-0424), and 18 combined.
- The logs correctly disclaim independent review, hosted runs and model enablement.
- The logs say "Final commit f8745047, working tree uncommitted". That was true historically. Claude published the code later, in `260beb49`.
- Three claims overstate what the code does:
  - PL-0421 log: "Suggestion serialization carries no raw evidence, paths". Provenance strings are unrestricted (F-3).
  - PL-0423 log: "checks ... target ± tolerance and deviation budget". It checks them against bounds the backend echoes back, not the user's own (F-1).
  - PL-0424 log: "absent/incomplete diagnostics ... remains review-required". Mesh topology that is partial or not applicable produces a clean status (F-2).

### Licensing, network and determinism (all 4 code modules)

- Imports are stdlib (`hashlib`, `json`, `math`, `re`, `dataclasses`, `datetime`, `enum`, `typing`) plus PackLab only.
- No model, weights or checkpoint. No network or download. No RNG and no wall clock.
- Collection sizes are bounded: families ≤ enum size, zone candidates ≤ 32, fit candidates ≤ 64, constraints ≤ 128.
- PL-0420 selects no model, and none was downloaded.
- These hold for all four modules.

## Findings

### P1

- **F-1 (PL-0423): acceptance trusts constraints and budget supplied by the backend.**
  - Where: `dimension_fit_proposal.py:330-360`.
  - `accept_dimension_fit_proposal` takes the target, tolerance and `maximum_deviation` from `proposal.request`. That request object is constructed and returned by the untrusted optimizer backend.
  - Acceptance only checks `model_revision_id` and the scan-master IDs. It never compares the request with the user-held request from `create_dimension_fit_request`.
  - Probe: the user measured height 102±5 and width 31±3 with a budget of 0.5. A backend echoed a request with `tolerance = 0.99*target` and `maximum_deviation = 1e9`. Acceptance succeeded and produced a successor with **height=3.0, width=1.0**.
  - This defeats the task's core property, "constrained by measured dimensions and scan deviation", and frozen criteria 2, 3 and 5.
  - Also, `deviation_evidence_sha256` is never verified at acceptance. Criterion 1 binding is therefore unenforced.
  - Fix: accept the user's `DimensionFitOptimizationRequest` (or its digest) as a parameter, require `proposal.request == request`, and add a regression test.

### P2

- **F-2 (PL-0424): a clean status is returned when mesh diagnostics are absent or not applicable.**
  - Where: `reconstruction_anomaly.py:116-162`.
  - Point-cloud statistics have `connected_component_count=None` and no `boundary_edge_count`/`nonmanifold_edge_count`. With a good confidence report, they yield `NO_RULE_TRIGGERED_DIAGNOSTIC_ONLY`. Probe confirmed this.
  - The same happens when `topology_indicators=()`, when a value is a bool or float (for example `boundary_edge_count=True` or `3.0`), and when `connected_component_count=True`. Malformed evidence is silently treated as "no defect".
  - This violates criterion 2 ("missing/incomplete diagnostic evidence map to ... findings") and criterion 4 ("cannot produce a clean pass").
  - Fix: emit an `*_incomplete` finding, or raise, when `geometry_kind != "triangle_mesh"`, when a topology key is missing, or when a value is mistyped.

- **F-3 (PL-0421, PL-0422, PL-0423): provenance fields accept paths and control characters.**
  - Where: `package_family_suggestion.py:72-76`, `profile_zone_proposal.py:93-97`, `dimension_fit_proposal.py:177-181`.
  - `backend_id`, `model_id`, `checkpoint_id` and `version` are only checked for strip and length ≤160.
  - Probe: `"C:\\Users\\owner\\models\\x.pt"` and `"a\nb\x00"` were both accepted and appear in `as_dict()` and the digest.
  - This violates the PL-0421/0422/0423 criteria "no paths ... serialize".
  - Fix: apply the existing `_ID` identifier regex, or the `_bounded_text` control-character check.

- **F-4 (PL-0421): accepting a suggestion for an asset whose family is OTHER always fails.**
  - Where: `package_family_suggestion.py:245, 256-259`.
  - When the current family is OTHER and the chosen family is not, the code sets the `other_family_label` provenance to UNKNOWN but keeps `updated_other_label = asset.other_family_label`.
  - Probe: `PackageFamilySuggestionError: asset_update_rejected:packaging_asset_other_family_label_provenance_required`.
  - It fails closed, so it is not a safety issue, but a legitimate user-confirmation path is broken and has no test.
  - Fix: set `updated_other_label = None` in that branch.

- **F-5 (PL-0421 to PL-0424): no feature flag or wired fallback.**
  - The repo has no feature-flag mechanism (grep found nothing), and no `apps/` or pipeline code imports these modules.
  - The modules are inert library contracts. In practice the "fallback" is that the existing manual path is unchanged and no backend is registered.
  - PL-0424 says "before fitting", but it is not wired into `captured_geometry_fit_gate` or any pre-fit step.
  - This does not literally meet the TASKS execution contract's "feature flag/fallback". The tracker should either record "disabled by construction: no backend registered and no caller" as the accepted prototype-tier flag, or add a minimal explicit gate.

- **F-6 (PL-0423): there is no optimizer.** The title is "Add fit-parameter optimizer". What exists is a contract plus explicit acceptance and a fake backend. There is no bounded reference optimizer, even a deterministic non-learned one (for example clamping each value to its target ± tolerance), so "Prototype a bounded ... solution" is only partly met. PL-0421 and PL-0422 are similarly contract-only. For PL-0422 this is the more defensible choice, because the model gate is open; it could still reuse `detect_design_profile_zones` as a deterministic reference proposer.

- **F-7 (tests are not discriminating enough): 8 of 16 mutants survived.**
  - PL-0421: removing the `other_family_label_not_allowed` rejection survived.
  - PL-0422: removing the transition-ordering check survived. Criterion 2 requires ordered transitions, and unordered input is never tested. The ordering is also re-checked downstream by `_validate_partition`, but this module's own rule is untested.
  - PL-0422: removing the zone-digest check survived. It is redundant behind the revision-ID check, so this is acceptable.
  - PL-0423: removing the constraint-set equality check survived, as did removing the scan-master ancestry check. The latter is redundant with the content-hashed model revision.
  - PL-0424: removing the non-manifold rule, removing the hole-report rule, and treating `not_evaluated` as clean all survived. All three are listed in criterion 2 but untested.
  - Killed: the stale revision check, the chosen-not-suggested check, USER_DECLARED provenance, the range check, the deviation budget, the tolerance check, the component threshold, and missing confidence.

### P3

- **F-8: raw exceptions instead of contract errors.**
  - An int too large for float as confidence or transition raises `OverflowError` (`package_family_suggestion.py:101`, `profile_zone_proposal.py:63`). PL-0423 handles this case correctly.
  - PL-0424: malformed `hole_report_linkage` raises `TypeError` (`reconstruction_anomaly.py:155`).
  - PL-0424: a NaN in the confidence payload raises a bare `ValueError` from `ReconstructionConfidenceReport.as_dict`.
  - All of these fail closed, but not through the contract error types.
- **F-9: acceptance binds to the suggestion/proposal object it is handed, not to a digest the user saw.** None of the three `accept_*` functions takes an expected `suggestion_sha256`/`proposal_sha256` parameter, although the digest is recorded. Criterion 4 of PL-0421 is met only by object identity. For a UI path, pass the displayed digest and compare it.
- **F-10 (PL-0424): the confidence report is not cross-bound to the geometry revision.** A confidence report for a different reconstruction can be paired with the statistics. I found no geometry ID in the confidence payload, so this needs a caller-level binding.
- **F-11 (PL-0420): the research doc omits the existing deterministic baseline.** Recommendation 3, "Build a deterministic geometry baseline", does not mention that `design_profile_zones.detect_design_profile_zones` already provides deterministic BASE/BODY/SHOULDER/NECK partitioning. The doc also gives no concrete licence facts for the candidate code (PointNet++/PTv3 repos). That is acceptable because nothing is selected, but checkpoint and code licence review remains an open gate.

## Per-criterion verification summary

### PL-0420

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. Distinguishes 2D segmentation, 3D part recognition and geometry detection | Pass | Decision summary and comparison table |
| 2. Compares ≥2 implementation paths | Pass | Four paths compared, with data/evaluation needs and a phased recommendation |
| 3. External claims cite primary sources | Pass | arXiv 1706.02413, arXiv 2312.10035, the Pointcept PTv3 repo, the Meta SAM 2 page and the Stanford page. Code and checkpoint licensing are explicitly separated. |
| 4. Privacy, deployment and authority boundaries | Pass | |
| 5. No model selected or downloaded | Pass | |
| 6. No private data | Pass | |

### PL-0421

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. No paths in serialization | Fail | F-3 |
| 2. Valid candidates | Pass | Bool, NaN and inf are rejected. Huge int raises a raw OverflowError (F-8). |
| 3. Non-authoritative | Pass | |
| 4. Explicit, stale-checked acceptance | Pass | Weak digest binding (F-9) |
| 5. Successor with USER_DECLARED provenance | Pass, except one path | The OTHER→X path is broken (F-4) |
| 6. Fake backend only | Pass | |

### PL-0422

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. No paths in serialization | Fail | F-3 |
| 2. Three finite, ordered transitions | Pass in code, not tested | Ordering is not tested (F-7) |
| 3. Non-authoritative | Pass | |
| 4. Explicit acceptance against exact revisions | Pass | Stale revision, forged zone digest and re-accept on a successor are all rejected (probed) |
| 5. Goes through `override_design_profile_zones` | Pass | Probed successor is `MANUAL_OVERRIDE`, `review_required=True`, `scan_master_replaced=False`, `DEFERRED_OWNER_VALIDATION`, `mold_use_authorized=False` |
| 6. Fake backend only | Pass | |

### PL-0423

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. Request binds revisions and evidence digests | Partial | `deviation_evidence_sha256` is never verified (F-1) |
| 2. Constraints are well formed | Pass at construction | Bypassable at acceptance (F-1) |
| 3. Candidates within target ± tolerance and budget | Fail | Bounds are backend-controlled (F-1) |
| 4. Non-authoritative serialization | Fail | F-3 |
| 5. Acceptance rejection cases | Fail in substance | Rejects only against the backend-echoed request (F-1) |
| 6. Goes through `revise_design_model_revision` | Pass | Successor keeps scan-master ancestry, `DEFERRED_OWNER_VALIDATION`, `mold_use_authorized=False` and `METRIC_UNVERIFIED` scale. No authority or scale upgrade. |
| 7. Backend values treated as untrusted | Stated, not enforced | F-1 |
| 8. Fake backend only | Pass | |

### PL-0424

| Criterion | Result | Evidence |
| --- | --- | --- |
| 1. Binding to geometry revision and digest | Pass | |
| 2. Findings for missing or incomplete evidence | Fail | F-2; rules partly untested (F-7) |
| 3. Deterministic, inputs not mutated | Pass | Probed: identical reports, input unchanged |
| 4. Missing evidence never yields a clean pass | Fail | F-2 |
| 5. Safe serialization | Pass | Odd observation/threshold strings are normalised to "unknown"; path-like revision IDs are rejected |
| 6. Synthetic fixtures only | Pass | |

## Verdicts

| Task | Verdict | Required before `[x]` |
| --- | --- | --- |
| **PL-0420** | **PASS** (research tier; eligible for CLAUDE_PEER_AUDITED_PASS) | Nothing blocking. Optional: fix F-11. A learned model stays externally gated on owner-approved data, exact code and checkpoint licences, and a pinned identity. |
| **PL-0421** | **CHANGES_REQUIRED** (minor) | F-3 provenance validation; F-4 fix for the OTHER→X label with a test; F-5 tracker disposition for the flag; test for the `other_family_label_not_allowed` path. |
| **PL-0422** | **CHANGES_REQUIRED** (minor) | F-3 provenance validation; unordered-transition test (F-7); F-5 disposition. The authority path is otherwise sound. |
| **PL-0423** | **CHANGES_REQUIRED** | F-1 (P1): bind acceptance to the user-held request or digest, and test a backend that widens the bounds. F-3. F-6: either add a deterministic bounded reference optimizer or narrow the claim in the tracker. Constraint-set mismatch test (F-7). |
| **PL-0424** | **CHANGES_REQUIRED** | F-2: handle point cloud, missing and mistyped topology as incomplete. Tests for the non-manifold, hole-report and `not_evaluated` rules (F-7). Contract errors for malformed input (F-8). F-5: wiring/flag disposition for "before fitting". |

**Must stay externally pending regardless of the code fixes:**

- Any real learned model or checkpoint for PL-0420..0423. This needs owner-approved training data, separate code and checkpoint licence review, a deployment and runtime review, and a pinned hash.
- Physical or metric validation of any accepted fit. Successors stay `DEFERRED_OWNER_VALIDATION`, and downstream geometry regeneration plus Scan Master comparison is required.
- Validation of the anomaly detector on real scans, which needs real PackScan captures.
