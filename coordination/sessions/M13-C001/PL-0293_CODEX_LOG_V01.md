# PL-0293 - Codex Implementation Log V01

Task: **Implement boolean feature support for handle openings and simple indentations**

Cycle: M13-C001  
Prompt: `PL-0293_CODEX_PROMPT_V01.md`  
Criteria: `PL-0293_CHATGPT_AUDIT_CRITERIA_V01.md`

## Authorization and synchronization

- Re-read root `TASKS.md` project status: M13-C001 ordered PL-0289 through PL-0309 batch; `READY`; required actor `CODEX`; no M14 authorization.
- Re-read the M13 master prompt and audit criteria, M12 `AUDITED_PASS`, ADR-0005, the M09 physical-validation deferral, PL-0291 and PL-0292 prompts, and both mandatory M12 feature source files.
- Starting local/origin SHA at child start: `1c896fed3fc0af1cd056d9e1127778029a67f631`; worktree was clean and synchronized before implementation.
- During implementation, `origin/main` advanced to `4c95b50788a8fec4ead8d940b821b8411955866a`. The only incoming path was the unrelated `docs/calibration/verification-records/2026-10-04-a4-owner-print-v01.md`.
- Preserved the local implementation commit, created the working branch from the refreshed `origin/main`, and cherry-picked the implementation commit without rebasing or force-pushing. The pre-sync commit remains on local branch `codex/m13-c001-pl0293-pre-sync`.
- Final implementation commit: `36f21d97264ebd85b0d641ba144f44003bfa1cdd`, parent `4c95b50788a8fec4ead8d940b821b8411955866a`.

## Files changed

- `core/src/packlab_core/cad_adapter.py`
- `core/src/packlab_core/cad_brep.py`
- `core/src/packlab_core/cad_boolean.py`
- `tests/core/test_cad_boolean.py`

No tracker, audit, prompt, criteria, dependency, lockfile, M14+, private scan, supplier, credential, or generated binary files were changed.

## Implementation

- Added a PackLab-owned CAD adapter path for constructing an explicit polygon prism and subtracting it from a registered opaque parent BREP. It validates parent authority, tool inputs, intersection, boolean completion, result topology, and single-solid output; failure diagnostics remain explicit.
- Added `cut_design_model_feature` for existing `HANDLE_OPENING` and `GRIP_INDENT` feature parameters only. It accepts a Design Model revision and BREP revision, never a Scan Master or triangle mesh.
- Handle-opening cuts use the explicit bounded profile and selected plane axes, with an explicit through-body BREP-bounds operation policy. Result metadata preserves `feature_hidden_extent_inferred=false`; the cut policy does not claim captured hidden-void extent.
- Grip-indent cuts use the persisted X/Z profile, explicit depth, side and Design Model front/back frame. They begin at the BREP surface and extrude only the requested depth.
- Deterministic operation IDs and BREP representation revisions retain tool/body feature IDs, source BREP and exact resulting Design Model revision. Parent authority mode, coordinate unit, scale state, `DEFERRED_OWNER_VALIDATION`, no-mold-use, and no-authority-promotion fields remain explicit.
- Added coverage for handle and indent cuts, repeatable provenance, feature linkage, outside/nonintersecting tools, invalid tool input, parent/model immutability, and rejection of non-BREP/raw-scan authority.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_cad_boolean.py tests/core/test_cad_brep.py tests/core/test_jerrycan_handle_opening.py tests/core/test_jerrycan_grip_indent.py` | All boolean and predecessor regressions pass. | PASS: 26 passed. |
| `uv run --locked pytest -q` | Locked full suite passes; any failing test blocks a green child. | PASS on final rerun: 1,524 passed, 6 skipped, 1 deselected, 2 existing duplicate-ZIP-name warnings. |
| `uv run --locked ruff check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py tests/core/test_cad_boolean.py` | Changed-file lint passes. | PASS. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py tests/core/test_cad_boolean.py` | Changed files are formatted. | PASS. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py` | Changed modules pass scoped typing. | PASS: no issues in 3 source files. |
| `uv run --locked mypy core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py` | Report changed and imported typing issues. | No diagnostics in changed modules. Four diagnostics surfaced in unmodified imports: two existing `calibration/marker_detection.py` errors and one each in `jerrycan_grip_indent.py` and `jerrycan_handle_void_candidates.py`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_brep.py core/src/packlab_core/cad_boolean.py tests/core/test_cad_boolean.py` | Changed sources compile. | PASS. |
| `uv lock --check` | Lock remains valid and unchanged. | PASS; no dependency or lockfile changes. |
| `git diff --check` | No whitespace errors. | PASS. |
| Credential/privacy/scope scan | No secrets, private evidence, downloads, unrelated scope or generated binaries. | PASS for changed paths; no credential-pattern matches. `TASKS.md`, audit files and all later-child paths remain unchanged. |

## Failures, fixes, and limitations

- Initial focused testing found a bounds tuple unpacking error; corrected the axis-aligned bounds mapping.
- Full-suite run one time failed in `test_unknown_marker_fails_collection` because its subprocess failed collection before reporting the intentionally unknown marker. The isolated guard then passed, and the final full-suite rerun passed.
- A short through-body prism margin triggered an OCCT sweep-constructor error. Expanded the prism beyond the BREP axis bounds using a deterministic 10% span margin; focused and final full tests pass.
- Unsilenced mypy still reports diagnostics in unmodified imported M12/calibration modules listed above. Scoped changed-module mypy passes.
- CAD topology and successful subtraction are software geometry evidence only. They do not establish hidden physical extent, physical accuracy, mold readiness, or manufacturing suitability. PL-0220 through PL-0224 remain deferred. PL-0289's HIGH native-library licensing/notice redistribution gate remains unresolved.

## Handoff

Implementation and this log are separate commits. This child has not been independently audited. The ordered M13 batch may continue only under the frozen master prompt and while green.

READY_FOR_INDEPENDENT_AUDIT
