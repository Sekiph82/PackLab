# PL-0235 - Codex Implementation Log V01

Task: **Implement scan-to-design distance heatmap contract**  
Cycle: **M10-C001**  
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CODEX_PROMPT_V01.md  
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0235_CHATGPT_AUDIT_CRITERIA_V01.md

## Synchronization and authorization

- Continuation V02 live tracker state: M10-C001 continuation PL-0235 through PL-0240, `READY`, `CODEX`; M11 remains unauthorized.
- Synchronized child starting SHA: `79fb484b9e7084188cafa52ccc0c6529f5d28593`, the published continuation master-log backfill commit on the fast-forward `origin/main` history.
- The initial checkout had three uncommitted PL-0235-only paths while `origin/main` advanced by three continuation authorization commits. Those edits were preserved; after verifying that the upstream commits touched only `TASKS.md` and the new continuation artifacts and that `geometry_adapter.py` was unchanged between the PL-0234 frontier and continuation tip, the edits were copied into a clean worktree at the authorized descendant and revalidated here.
- Before implementation publication, `git fetch origin main` reported one local commit ahead and zero behind. `git push origin HEAD:main` succeeded; the implementation commit is now on GitHub `main`.
- M09 accepted frontier remains PL-0202 through PL-0219. PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`, not passed.

## Inputs read

- M10 continuation V02 work order and matching V02 audit criteria.
- Original M10 master work order and audit criteria; M10 continuation master log.
- PL-0235 V01 child prompt and matching audit criteria.
- PL-0233 Scan Master authority pre-read.
- M09 accepted partial audit and owner physical-validation deferral decision.
- `coordination/MILESTONE_BATCH_PROTOCOL.md`, `coordination/README.md`, and `coordination/AUDIT_POLICY.md`.

## Files changed

- `core/src/packlab_core/geometry_adapter.py`
- `core/src/packlab_core/scan_design_heatmap.py` (new)
- `tests/core/test_scan_design_heatmap.py` (new)

No task tracker, audit verdict, dependency/lockfile/license file, captured source artifact, private scan, generated binary, or M11 implementation was changed.

## Implementation

Added a deterministic PackLab-owned Scan Master to explicitly supplied fitted Design Model comparison contract. The Design Model reference pins its project, exact fitted Scan Master revision, geometry digest, coordinate frame, inherited scale state and scale-provenance ID. The service validates the selected Scan Master manifest through the existing registration factory and does not fit, register, mutate or retarget either geometry.

The service samples source vertices with a bounded deterministic even-index rule and queries exact point-to-triangle distances through the existing pinned Open3D adapter. Unsigned distances support open target meshes. Signed mode follows the explicit inside-negative policy and is allowed only for a watertight, non-self-intersecting target. Policy thresholds, sample indices/count, parents/digests, scale/frame/provenance, units, distances and deterministic color-bin RGBA metadata are recorded in the result identity and serialization.

Relative inputs retain `reconstruction_units`; metric-unverified inputs retain `mm_unverified`. Physical status remains `DEFERRED_OWNER_VALIDATION`, mold use remains false, and the output labels the values as geometry deviation only, not manufacturing tolerance. No M11 fitting code was added.

## Validation evidence

| Command | Expected / failure condition | Actual |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_scan_design_heatmap.py tests/core/test_geometry_adapter.py tests/core/test_repeat_scan_registration.py tests/core/test_scan_master.py tests/core/test_geometry_statistics.py tests/core/test_normalization_transform.py tests/core/test_physical_accuracy_benchmark.py tests/calibration/test_scale_provenance.py` | New comparison behavior plus Scan Master, adapter, registration, geometry and scale predecessors pass; any test failure blocks this child. | Passed: `57 passed in 6.09s`. Includes zero/known offset, mixed signed distances, open-target rejection, deterministic identity, sampling/bin thresholds, stale parent, coordinate/scale mismatch, unverified units and deferred/mold non-claims. |
| `uv run --locked pytest -q` | Exact locked full repository suite exits 0; any failure blocks this child. | Passed: `1212 passed, 6 skipped, 1 deselected, 2 warnings in 27.30s`. The warnings are existing duplicate ZIP fixture names in PackScan and transfer validation tests. |
| `uv run --locked ruff check core/src/packlab_core/geometry_adapter.py core/src/packlab_core/scan_design_heatmap.py tests/core/test_scan_design_heatmap.py` | Changed-file lint is clean. | Passed: `All checks passed!`. |
| `uv run --locked ruff format --check core/src/packlab_core/geometry_adapter.py core/src/packlab_core/scan_design_heatmap.py tests/core/test_scan_design_heatmap.py` | Changed files are formatted. | Passed: `3 files already formatted`. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/geometry_adapter.py core/src/packlab_core/scan_design_heatmap.py` | Adapter and comparison service type-check. | Passed: `Success: no issues found in 2 source files`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/geometry_adapter.py core/src/packlab_core/scan_design_heatmap.py tests/core/test_scan_design_heatmap.py` | Changed Python files compile; nonzero exit blocks this child. | Passed, exit 0. |
| `git diff --check` and staged diff check | No whitespace errors. | Passed; Git emitted only expected Windows LF-to-CRLF notices. |
| Changed-path, credential/private-key, and future-scope scans | Only the three authorized PL-0235 paths; no credential/private-key pattern or M11/later-child code. | Passed: exactly three changed paths, scans clean. No dependency, license, tracker or audit path changed. |

## Failures and fixes

Initial static checks identified unsorted imports, formatting, optional Open3D callable narrowing and a one-sample tuple inference issue. These were corrected within the PL-0235 implementation; rerun Ruff, format check, mypy, compileall and diff check all passed. No test failures remained.

## Limitations and authority boundaries

- Signed distance depends on Open3D's signed-distance convention and is restricted to a closed watertight, non-self-intersecting target; unsigned mode remains available for open meshes.
- Distances use inherited coordinate units. `mm_unverified` is not verified physical measurement. The synthetic fixtures do not establish physical accuracy, manufacturing tolerance or mold suitability.
- No physical benchmark, PL-0220 through PL-0224 owner validation, or M11 fitting was performed.

## Publication

- Implementation/evidence commit: `c58cc0874fb5ac12982dc529cdb1a7ce6adeb191` (`Add scan-to-design deviation heatmap contract`).
- `git push origin HEAD:main` succeeded. The child-log-only commit follows separately.
- Secrets/privacy review: the three changed paths contain only synthetic fixtures and implementation; credential/private-key scan clean.
- Final child status: implementation checks green; awaiting independent ChatGPT audit. This is not acceptance.

READY_FOR_INDEPENDENT_AUDIT
