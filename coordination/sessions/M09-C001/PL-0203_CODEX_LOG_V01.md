# PL-0203 - Codex Implementation Log V01

Task: **Estimate global reconstruction scale from physical marker geometry**

Date: 2026-10-02

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M09-C001/PL-0203_CHATGPT_AUDIT_CRITERIA_V01.md

## Repository and authorization

- Repository root: `C:/Users/sekip/Desktop/PackLab`
- Branch/remote: `main` / `https://github.com/Sekiph82/PackLab.git`
- Live tracker rechecked: M09-C001 ordered `PL-0202` through `PL-0224`, `READY`, `CODEX`.
- Starting synchronized SHA: `ed63ab605c5270d695d7d1eb8f19a60a9e5df5af`.
- Per-child sync: `git fetch origin main --prune`; divergence `0 0`, clean before edits.
- Master prompt/criteria, coordination policies, accepted M08 audit, and this child's prompt/criteria were read.
- Mandatory pre-reads read: `docs/calibration/scale-estimation.md`, `docs/calibration/synthetic-ground-truth.md`, `docs/implementation/PL-0209_METRIC_SCALE_PROVENANCE.md`, and the latter's required `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md`.
- No conflict was found: the architecture and PL-0209 specification require camera-linked reconstructed geometry, explicit physical provenance, and no metric promotion without accepted physical authority.

## Implementation

Added `reconstruction_scale.py`, a separate estimator that compares explicit 3D reconstructed marker-edge lengths with versioned known marker references. It consumes PL-0202 camera-bound observations and checks marker identity, reconstruction revision, camera-solution revision, coordinate units, source identity digest, and reference units. A versioned median-residual policy identifies outliers; the result records used/rejected observation digests, per-observation residuals, uncertainty, math/policy versions, and parent revisions. It never calls the existing image-space `mm_per_pixel` estimator. Synthetic fixtures are labeled `synthetic_test_fixture`; every result remains `METRIC_UNVERIFIED`.

Changed files:

- `core/src/packlab_core/calibration/reconstruction_scale.py` (new)
- `core/src/packlab_core/calibration/__init__.py`
- `tests/calibration/test_reconstruction_scale.py` (new)

No runtime/development dependency, private capture, generated geometry, physical measurement, or M10 work was added. `TASKS.md`, RAW_CAPTURE, accepted M08 artifacts, and audit-owned files remain unchanged.

## Validation evidence

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/calibration/test_reconstruction_scale.py tests/calibration/test_scale_estimation.py tests/calibration/test_synthetic_ground_truth.py tests/calibration/test_marker_association.py` | New estimator plus prior detector/image-scale/synthetic contracts pass. | `30 passed, 3 skipped`. |
| `uv run --locked pytest -q` | Exact locked full suite exits 0; a failure blocks PL-0203. | Exit 0; `998 passed, 7 skipped, 1 deselected, 2 warnings` in 16.77s. Existing duplicate ZIP-entry fixture warnings came from `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py`. |
| `uv run --locked ruff check core/src/packlab_core/calibration/reconstruction_scale.py core/src/packlab_core/calibration/__init__.py tests/calibration/test_reconstruction_scale.py` | No changed-file lint errors. | Passed. |
| `uv run --locked ruff format --check core/src/packlab_core/calibration/reconstruction_scale.py core/src/packlab_core/calibration/__init__.py tests/calibration/test_reconstruction_scale.py` | All changed Python files formatted. | Passed. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/calibration/reconstruction_scale.py` | New scale contract type-checks. | Passed: `Success: no issues found in 1 source file`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/calibration/reconstruction_scale.py core/src/packlab_core/calibration/__init__.py tests/calibration/test_reconstruction_scale.py` | Changed Python files compile. | Passed, exit 0. |
| `git diff --check` and `git diff --cached --check` | No whitespace errors. | Passed. |
| `git diff -- TASKS.md`, changed-file scope review, and credential-pattern scan | Tracker unchanged; only three authorized files; no credential/private-key patterns. | Passed. No dependencies or generated/binary artifacts were added. |

Coverage includes exact synthetic 0.4 mm/reconstruction-unit scale, noisy edges, inconsistent/outlier observations, insufficient observations, wrong units, stale reconstruction and camera revisions, stable ordering, uncertainty/residual evidence, and the invariant that synthetic results remain `METRIC_UNVERIFIED`.

## Publication

- Implementation commit: `39cf2b48f98592b680e9f66a14b55a31ba7c4237` (`calibration: estimate global reconstruction scale`).
- Pushed to `origin/main`; fetch confirmed local `HEAD` and `origin/main` both equal `39cf2b48f98592b680e9f66a14b55a31ba7c4237` before the log-only commit.
- No owner work was overwritten. No audit verdict was created.

READY_FOR_INDEPENDENT_AUDIT
