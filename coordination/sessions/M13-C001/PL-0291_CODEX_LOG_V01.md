# PL-0291 - Codex Implementation Log V01

Task: **Convert profile/revolve Design Models into BREP solids**
Cycle: **M13-C001**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0291_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live GitHub `TASKS.md` and the M13 master authorize M13-C001 / PL-0289 through PL-0309 / READY / CODEX. M12 remains `AUDITED_PASS`; PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`; M14+ remains unauthorized.
- PL-0290 implementation/log and master checkpoint are published. This child began at `730f1991f32c3084758e3dd91c27d33e1f1cd409`, equal to refreshed `origin/main` (0 ahead / 0 behind). Canonical Desktop owner-local files remain preserved outside the isolated managed worktree.
- Read the M13 master prompt/criteria, PL-0291 prompt/criteria, PL-0290 prompt, M12 audit, ADR-0005, M09 physical-validation deferral, dependency/license register, and required design operation/profile/model source files.

## Implementation

- Extended `core/src/packlab_core/cad_adapter.py` with a binding-hidden revolve builder. It accepts the exact PackLab `DesignModelRevision`, `DesignProfile`, and `DesignOperation`; validates the source model, profile/operation IDs, stable feature references, parent/unit/physical authority, full sweep, finite unit axis, and bounded sample count; and creates a valid single-solid BREP without exposing an OCP class.
- Profile curves are represented by deterministic, uniformly sampled axial/radial points, closed to the revolve axis, and built as a planar profile face before the 360-degree revolve. Self-intersecting, interior-axis-touching, and degenerate profile boundaries fail closed. The revision metadata records the sampling method and exact sample count; it makes no physical-accuracy claim.
- The adapter validates BREP topology and exactly one solid, serializes the BREP for a SHA-256 geometry digest, creates a deterministic opaque PackLab shape handle pinned to the model/profile/operation/digest, and retains the backend object only inside the private adapter registry for downstream adapter work in the current runtime.
- Added `CadBrepRepresentationRevision` and `revolve_design_model_to_brep` in `core/src/packlab_core/cad_brep.py`. The derived revision ID binds geometry digest, exact Design Model revision, operation, parent authority kind/revision, scale/unit state, physical status, handle, and sample count. `as_dict()` explicitly states that the revision does not replace the Design Model or promote Scan Master authority.
- Added coverage for a cylindrical bottle revolve; repeated deterministic geometry/revision/handle digests; captured and standalone parents under both `RELATIVE/reconstruction_units` and `METRIC_UNVERIFIED/mm_unverified`; stale model/profile/partial-sweep rejection; degenerate/interior-axis and self-intersecting profiles; feature references; backend type hiding; physical/mold authority preservation; and Design Model immutability.

## Files changed

- `core/src/packlab_core/cad_adapter.py`
- `core/src/packlab_core/cad_brep.py`
- `tests/core/test_cad_brep.py`
- `coordination/sessions/M13-C001/PL-0291_CODEX_LOG_V01.md` (this log only)

Implementation commit: recorded below after publication.

## Validation commands and results

| Command/check | Expected result / failure condition | Actual result |
| --- | --- | --- |
| `uv run --locked pytest -q tests/core/test_cad_brep.py tests/core/test_cad_adapter.py tests/core/test_design_operations.py tests/core/test_revolved_design_model.py` | BREP, authority, operation and M11 revolve regressions pass. | PASS: 29 passed. |
| `uv run --locked pytest -q` | Full locked project suite passes. | PASS: 1,512 passed, 6 skipped, 1 deselected, 2 existing duplicate-ZIP-name warnings. |
| `uv run --locked ruff check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py tests/core/test_cad_brep.py` | Changed Python files pass Ruff. | PASS. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py tests/core/test_cad_brep.py` | Changed Python files are formatted. | PASS. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py` | Changed adapter/revision modules type-check. | PASS: no issues in 2 source files. |
| `uv run --locked mypy core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py` | Report changed-module and imported typing issues. | Changed modules are clean; two existing errors remain in `calibration/marker_detection.py` lines 112 and 140. PL-0289 already recorded 28 whole-tree baseline errors across 9 unrelated files. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py tests/core/test_cad_brep.py` | Changed Python sources compile. | PASS. |
| `uv lock --check` | Lock remains valid; fail on dependency drift. | PASS; no dependency or lockfile changed. |
| `git diff --check` | No whitespace errors. | PASS. |
| Runtime BREP probe | Cylinder profile produces valid one-solid BREP; deterministic repeated digest/revision and retrievable opaque handle. | PASS on selected PL-0289 OCP 7.9.3.1.1 / OCCT 7.9.3 runtime. |
| Changed-file scope, credential, privacy, and runtime-download scans | Only PL-0291 source/tests/log; no secret/private evidence/new dependency/download fallback. | PASS; only the already locked OCP imports are present; no credential patterns found. `TASKS.md`, audit artifacts, license/dependency decisions, and M14+ files are unchanged. |
| Remote boundary | Fetch `origin/main`; publish fast-forward commits and verify remote SHAs. | Before implementation publication, `git fetch origin main` succeeded and reported 0 ahead / 0 behind. Final SHA recorded after push. |

## Failures, fixes, limitations

- Initial focused runs exposed an adapter helper placement error, a revision hash computed before default contract values were initialized, and a stale-model fixture that was identical by deterministic identity. Corrected the helper, explicitly included contract defaults in revision hashing, and gave the stale fixture distinct source provenance. Subsequent focused/predecessor tests pass.
- An integration test initially omitted its `DesignProfile` import; corrected before final validation.
- Unsilenced targeted mypy continues to surface only the two pre-existing `marker_detection.py` errors. Changed modules pass the scoped follow-imports-silent check.
- The BREP surface follows a deterministic 257-sample profile polyline approximation by default; it is not a physical metrology result or mold/manufacturing authorization. The private opaque shape registry is process-local; after process restart the BREP must be regenerated from the exact Design Model/profile/operation inputs.
- PL-0289's HIGH native-library licensing/notice redistribution gate remains in force. This child does not alter the dependency choice or clear redistribution.

Implementation commit: `8318bde16393b5c4240a34bba910da766800a501`

## Handoff

Implementation and this log are published in separate commits. This child has not been self-audited. The ordered batch may continue only under the frozen master protocol and while green.

READY_FOR_INDEPENDENT_AUDIT
