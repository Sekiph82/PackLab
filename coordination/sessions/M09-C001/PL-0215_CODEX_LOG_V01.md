# PL-0215 - Codex Implementation Log V01

Task: **Measure neck and finish candidates**

Date: 2026-10-02

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0215_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0215_CHATGPT_AUDIT_CRITERIA_V01.md

## Repository and authorization

- Repository root: `C:/Users/sekip/Desktop/PackLab`.
- Branch/remote: `main` / `https://github.com/Sekiph82/PackLab.git`.
- Live tracker rechecked: M09-C001 ordered `PL-0202` through `PL-0224`, `READY`, `CODEX`.
- Starting synchronized SHA: `284aeb7d1eb6558846b65edaf2f173aea4348a86`.
- Per-child sync: fetched `origin/main`; divergence `0 0`, clean before edits.
- Master prompt/protocol, repository coordination policies, accepted M08 audit, and this child prompt/criteria were read.
- Mandatory pre-read read in full: `docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md`.

## Implementation

Added `core/src/packlab_core/neck_finish_candidates.py` and `tests/core/test_neck_finish_candidates.py`. Each observation binds a `HorizontalSection` to its `CrossSectionMeasurement`; the service also requires a `VerticalProfile`. All evidence must match the current source geometry, normalized revision, scale-provenance ID, scale state and coordinate units. Section Z must match the fitted measurement plane within the declared Z tolerance; every section and the vertical profile must have minimum captured support.

The versioned candidate method computes each plane's equivalent radius as `sqrt(major_radius * minor_radius)`, partitions adjacent planes into radius bands using the configured maximum relative adjacent-radius change, and compares each supported band's median radius with the largest supported radius. Bands meeting the configured minimum reduction and support thresholds are emitted as `NARROW_REGION_CANDIDATE`, ranked by greater relative radius reduction, then smaller median radius, then lower Z. Each output contains plane Z values/range, estimated radii/diameters, height, support counts, maximum fit/planarity residuals and scale-factor uncertainty inputs. Fit residuals are explicitly not confidence intervals. All candidates require review, and multiple candidates also carry an ambiguity review flag.

The service does not identify which candidate is a neck or finish, infer thread/closure standards, claim mold-ready dimensions, or promote scale state. Relative units remain `reconstruction_units`; metric-unverified units remain `mm_unverified`.

Changed files:

- `core/src/packlab_core/neck_finish_candidates.py` (new)
- `tests/core/test_neck_finish_candidates.py` (new)
- `coordination/sessions/M09-C001/PL-0215_CODEX_LOG_V01.md` (this log; separate log-only commit)

No dependency, model, hosted service, private capture, physical measurement, generated geometry, later-child, or M10 work was added. `TASKS.md`, audit-owned files, RAW_CAPTURE, accepted M08 artifacts, and dependency manifests are unchanged. Credential-pattern scan returned no matches. The implementation commit contained only the two authorized Python files.

## Validation evidence

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_neck_finish_candidates.py tests/core/test_vertical_profile.py tests/core/test_horizontal_section.py tests/core/test_cross_section_measurement.py tests/core/test_two_point_measurement.py tests/core/test_bounding_dimensions.py tests/core/test_normalization_transform.py tests/calibration/test_scale_provenance.py` | Candidate analysis and predecessor section/profile/measurement/scale contracts pass. | Passed: `66 passed`. |
| `uv run --locked pytest -q` | Exact locked full suite exits 0; any failed test blocks PL-0215. | Exit 0: `1103 passed, 7 skipped, 1 deselected, 2 warnings` in 16.26s. Existing duplicate ZIP-entry warnings remain in `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py`. |
| `uv run --locked ruff check core/src/packlab_core/neck_finish_candidates.py tests/core/test_neck_finish_candidates.py` | No changed-file lint errors. | Passed: `All checks passed!`. |
| `uv run --locked ruff format --check core/src/packlab_core/neck_finish_candidates.py tests/core/test_neck_finish_candidates.py` | Changed Python files formatted. | Passed: both files already formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/neck_finish_candidates.py` | New service type-checks. | Passed: `Success: no issues found in 1 source file`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/neck_finish_candidates.py tests/core/test_neck_finish_candidates.py` | Changed Python files compile. | Passed, exit 0. |
| `git diff --check` and `git diff --cached --check` | No whitespace errors. | Passed. Git emitted only its CRLF conversion notice for the new Python files. |
| `git diff --cached --name-only`, protected-file/dependency guard, and credential-pattern scan | Only authorized files changed; trackers and dependencies untouched; no credential pattern. | Passed. Exactly two Python files were staged for implementation; protected-file/dependency guards had no diff; credential scan returned no matches. |

Coverage includes a synthetic bottle with body, neck and finish candidate bands; multiple/ambiguous candidates; exact threshold inclusion; insufficient section evidence; deterministic ranking independent of evidence input order; parent/profile/section provenance matching; relative and metric-unverified units; residual/support output; and explicit no-thread-standard/no-closure/no-mold-ready claims. No owner physical evidence was used or fabricated.

## Publication

- Implementation commit: `1e10d3ed550d99c3cff5567746784137c1b60f89` (`Implement PL-0215 conservative neck finish candidates`).
- Pushed to `origin/main`; fetch confirmed local `HEAD` and `origin/main` both equal `1e10d3ed550d99c3cff5567746784137c1b60f89` before the log-only commit.
- No owner work was overwritten. No audit verdict was created.

READY_FOR_INDEPENDENT_AUDIT
