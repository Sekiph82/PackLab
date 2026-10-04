# PL-0281 Codex Implementation Log V01

Task: **Allow swapping trigger/pump variants without modifying bottle geometry**

Cycle: `M12-C001`
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0281_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M12-C001/PL-0281_CHATGPT_AUDIT_CRITERIA_V01.md

## Synchronization and commits

- Starting synchronized SHA: `2df2714cd551aa4c4dad02ed3bfd909d32030fab`.
- Before implementation, the clean detached M12 worktree matched `origin/main` (`0` ahead / `0` behind). The Desktop owner checkout was not modified.
- Implementation/evidence commit: `fa24e5cd76db1e5b3ba633f94ff1dbe7739e9c17`.
- The implementation commit was pushed independently before this child log. `git ls-remote origin refs/heads/main` returned `fa24e5cd76db1e5b3ba633f94ff1dbe7739e9c17`.
- This child log is published in a separate log-only commit.

## Authorization and pre-reads

- Re-read live root `TASKS.md`, M12 master, PL-0281 V01 prompt/criteria, accepted M11 milestone audit, and M09 physical-validation owner deferral.
- Confirmed M12-C001 R01 remains `CHANGES_REQUIRED` / `CODEX`, authorizes continuation through PL-0288, and says not to start M13. No tracker or audit file was changed.
- Read mandatory PL-0277 and PL-0278 prompts and criteria, plus the PL-0277 importer and PL-0278 alignment contracts needed for exact component, stable feature and attachment semantics.
- Frozen scope: replace one exact trigger/pump variant only when its `TRIGGER_PUMP` feature preserves the existing stable attachment semantic and the variant preserves the pump's exact Scan Master, digest, scale and provenance. Preserve the body and closure Design Models unchanged; explicitly revision the dip tube to pin the new pump revision; create a new immutable assembly graph and linked swap record.

## Changed files

- `core/src/packlab_core/assembly_variant_swap.py`
- `tests/core/test_assembly_variant_swap.py`

## Implementation

- Validates the current assembly graph, expected current graph/tube/candidate IDs, exact old tube-to-pump reference, current and candidate trigger/pump feature kinds, and matching stable attachment semantic key. Parent, Scan Master digest, unit, scale and scale provenance must remain compatible.
- Rebinds the existing dip-tube path/length/diameter to the exact candidate pump model/feature through the existing immutable Design Model edit boundary. Path and dimensions are preserved; only the attachment and resulting component revision identity change.
- Creates a new validated assembly graph with the candidate pump and revised dip tube. Body/closure inputs are reused without modification. The swap revision records previous/new graph and pump/tube revisions, preserved body revisions and body Scan Master ancestry; it makes no geometry adaptation.
- Added bounded immutable graph-snapshot history with undo/redo and redo invalidation after a new branch edit. Old graph and component snapshots remain intact and addressable.
- Output retains `DEFERRED_OWNER_VALIDATION`, `mold_use_authorized: false`, and false physical/manufacturing compatibility claims. Stable attachment-semantic continuity is metadata only, not a physical fit result.

## Validation

Expected: a current candidate with matching stable outlet semantic and exact inherited pump ancestry creates a deterministic new assembly revision; incompatible/stale variants fail closed; body/closure and captured-parent bytes remain unchanged; the previous assembly is retained and undo/redo returns the exact immutable snapshots. Any failed invariant blocks batch continuation.

| Check | Command | Result |
|---|---|---|
| Focused swap and predecessor regressions | `uv run --locked pytest -q tests/core/test_assembly_variant_swap.py tests/core/test_assembly_clearance.py tests/core/test_assembly_graph.py tests/core/test_dip_tube.py tests/core/test_closure_workflow.py` | Passed: 23 tests. |
| Changed-file Ruff | `uv run --locked ruff check core/src/packlab_core/assembly_variant_swap.py tests/core/test_assembly_variant_swap.py` | Passed: all checks passed. |
| Changed-file formatting | `uv run --locked ruff format --check core/src/packlab_core/assembly_variant_swap.py tests/core/test_assembly_variant_swap.py` | Passed: both files already formatted. |
| Targeted mypy | `uv run --locked mypy --follow-imports=silent core/src/packlab_core/assembly_variant_swap.py` | Passed: no issues found in 1 source file. |
| Compile | `uv run --locked python -m compileall -q core/src/packlab_core/assembly_variant_swap.py tests/core/test_assembly_variant_swap.py` | Passed: exit 0. |
| Patch whitespace | `git diff --check` and staged `git diff --cached --check` | Passed: no whitespace errors. |
| Locked full suite at final implementation content | `uv run --locked pytest -q` | Passed: 1,449 passed, 6 skipped, 1 deselected, 2 duplicate-ZIP-name fixture warnings; 48.14s. Exit code 0. |
| Secret/backend/network scan | `rg -n -i 'api[_-]?key|token|secret|private key|supplier|raw scan|open cascade|cadquery|freecad|urlopen|requests\.get|http[s]?://' core/src/packlab_core/assembly_variant_swap.py tests/core/test_assembly_variant_swap.py` | No hits. |
| Scope/dependency/license/privacy/generated/binary review | Reviewed the exact two changed Python paths and staged diff. | No dependency/lock/license change, private/raw data, external asset, generated binary, CAD backend, M13, or later-child implementation. Tests use synthetic temporary PackLab fixtures. |
| Remote visibility | `git fetch origin main`; `git push origin HEAD:main`; `git ls-remote origin refs/heads/main` | Passed: implementation SHA `fa24e5cd76db1e5b3ba633f94ff1dbe7739e9c17` is visible on GitHub main. |

## Failures and fixes

- The first focused run found a stale tuple-unpack in the new test helper after the fixture was extended to return its parent binding. The test unpack was corrected; the final focused and full runs pass.
- Final static review and all implementation invariants pass. No unresolved failures remain.

## Limitations and authority

- Compatibility is limited to exact metadata parent/unit/scale checks and stable attachment-semantic continuity. It is not evidence of geometric, thread, seal, fluid, physical or manufacturing fit.
- The dip tube receives a new Design Model revision solely to pin the candidate pump revision; authored path, length and diameter parameters are preserved. Prior graph and tube revisions remain immutable in history.
- Body and closure Design Models and the body Scan Master parent/digest are unchanged. `METRIC_UNVERIFIED` remains unverified; physical validation is deferred; mold use is unauthorized.
- No private/unlicensed asset, network download, CAD/BREP/STEP work, physical claim or M13 implementation was introduced.

READY_FOR_INDEPENDENT_AUDIT
