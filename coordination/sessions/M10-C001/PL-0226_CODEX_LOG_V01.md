# PL-0226 - Codex Implementation Log V01

Task: **Remove isolated floating components with configurable safeguards**

Date: 2026-10-02

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M10-C001/PL-0226_CHATGPT_AUDIT_CRITERIA_V01.md

## Repository and authorization

- Repository root: `C:/Users/sekip/Desktop/PackLab`.
- Branch/remote: `main` / `https://github.com/Sekiph82/PackLab.git`.
- Live tracker rechecked: M10-C001 ordered `PL-0225` through `PL-0240`, `READY`, `CODEX`; M11 is unauthorized.
- Synchronized starting SHA: `ff6e8e374eeb2ab5bee896e2436a99ae863bd300`; `git fetch origin main` showed 0 ahead / 0 behind and clean worktree before PL-0226 edits.
- Re-read M10 master prompt and criteria, batch protocol, coordination/audit policy, accepted M09 partial audit, M09 owner physical-validation deferral decision, PL-0226 prompt and criteria. Confirmed PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`, not passed.
- PL-0226 mandatory pre-read `docs/implementation/PL-0233_SCAN_MASTER_AUTHORITY.md` was read in full; its required `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md` pre-read had already been read in full before PL-0225.

## Implementation

Added `core/src/packlab_core/component_cleanup.py` to analyze `TriangleMeshData` from the PackLab-owned geometry adapter and create a deterministic child revision. Connectivity is explicitly `triangles_share_edge_v1`; vertex-only contact does not join components. The versioned policy marks components with triangle counts strictly below `minimum_component_triangles` as candidates, always preserves the largest component (ties go to the first input triangle index), and caps the configured maximum removable fraction at 10% of parent triangle count. The removal boundary is inclusive. No distance threshold applies to this edge-connectivity policy.

The cleanup is non-mutating. It fails closed for meshes without triangles, unreferenced vertices, all-small/ambiguous components, missing unverified-scale provenance, metric-verified inputs, and removal beyond the configured cap. It emits deterministic component ordering, removed triangle indices/counts, parent and output geometry SHA-256 digests, exact parent revision ID, versioned parameters, and a content-derived child revision ID. Retained vertices and their colors/normals are compacted and remapped in stable input order.

The child record carries the input scale state and scale-provenance ID unchanged, stamps `physical_accuracy_validation_status=DEFERRED_OWNER_VALIDATION`, and sets `mold_use_authorized=false`. It makes no physical accuracy, manufacturing suitability, or metric verification claim. No generated or private geometry was introduced.

Tests cover a synthetic main component plus floaters, support-threshold boundary, all-small failure, removable-fraction boundary and excess, deterministic ordering/identity, parent immutability, provenance/digests, `METRIC_UNVERIFIED` retention and physical deferral, metric-state escalation rejection, unsafe policy rejection, unreferenced-vertex ambiguity, and empty mesh failure.

Changed implementation files:

- `core/src/packlab_core/component_cleanup.py`
- `tests/core/test_component_cleanup.py`

No dependency, license register, `TASKS.md`, audit artifact, RAW_CAPTURE, reconstruction, OBJECT_CAPTURE_GEOMETRY, owner/private scan, later-child implementation or M11 work was changed.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_component_cleanup.py` | Main-plus-floaters, threshold, ambiguity, fraction cap, deterministic order, immutability, provenance and deferred scale cases pass. | Passed: `10 passed in 0.07s`. Initial draft used test caps above the policy's 10% maximum; the test fixtures were corrected before final green run. |
| `uv run --locked pytest -q tests/core/test_component_cleanup.py tests/core/test_geometry_adapter.py tests/core/test_mesh_refinement.py tests/core/test_mesh_reconstruction.py tests/core/test_normalization_transform.py tests/core/test_physical_accuracy_benchmark.py tests/calibration/test_scale_provenance.py` | PL-0226 plus adapter and predecessor mesh/scale regressions pass. | Passed: `157 passed in 1.66s`. |
| `uv run --locked pytest -q` | Exact locked full repository suite exits 0; any failure blocks PL-0226. | Exit 0: `1147 passed, 6 skipped, 1 deselected, 2 warnings in 30.29s`. Existing duplicate ZIP filename warnings in `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py`. |
| `uv run --locked ruff check core/src/packlab_core/component_cleanup.py tests/core/test_component_cleanup.py` | Changed Python files lint clean. | Passed: `All checks passed!`. |
| `uv run --locked ruff format --check core/src/packlab_core/component_cleanup.py tests/core/test_component_cleanup.py` | Changed Python files formatted. | Passed: both files already formatted. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/component_cleanup.py` | New module type-checks. | Passed: `Success: no issues found in 1 source file`. Initial draft exposed two tuple-shape typing errors, fixed and rechecked. |
| `uv run --locked python -m compileall -q core/src/packlab_core/component_cleanup.py tests/core/test_component_cleanup.py` | Changed Python files compile. | Passed, exit 0. |
| `git diff --check`, `git diff --cached --check` | No whitespace errors. | Passed. Git emitted only CRLF conversion notices for new files. |
| Exact changed-path review and credential/private-key pattern scan | Only PL-0226 implementation/test paths changed; no secret or private-key pattern. | Passed: exactly two implementation paths; credential-pattern scan clean across both. |

No physical validation or accuracy benchmark was run. Synthetic geometry tests establish code behavior only and do not close owner validation.

## Publication

- Implementation commit: `c6c5da6cc6dc27d2a2259572211bbf20b474930a` (`Add safeguarded mesh component cleanup`).
- Pushed to `origin/main`; fetch confirmed local `HEAD` and `origin/main` both equal `c6c5da6cc6dc27d2a2259572211bbf20b474930a` before this child-log commit.
- No owner work was overwritten. No audit verdict was created.

READY_FOR_INDEPENDENT_AUDIT
