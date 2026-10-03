# PL-0265 - Codex Implementation Log V01

Task: **Add cap visibility and replacement workflow**

Cycle: `M11-C001`

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M11-C001/PL-0265_CHATGPT_AUDIT_CRITERIA_V01.md

## Synchronization and commits

- Starting synchronized commit: `b5d6fbd6e759af04a256b5dcd7bb2ad0c68d3f29`.
- Fetched `origin/main`; local `HEAD`, fetched `origin/main`, and remote main matched; divergence `0 0`; worktree clean before implementation.
- Implementation/evidence commit: `d5f7f49b1bdc2369b15044b176605e42d7088a77`.
- Before push, fetched origin main remained at the starting commit. `git push origin HEAD:main` succeeded.
- `git ls-remote origin refs/heads/main` returned `d5f7f49b1bdc2369b15044b176605e42d7088a77`.
- This child log and the master-index update are published as separate commits. This file does not claim its own containing commit SHA.

## Authorization and files read

- Live `TASKS.md` Project Status authorized `M11-C001 — Ordered Batch PL-0241 through PL-0267`, status `READY`, required actor `CODEX`, tracking repository `Sekiph82/PackLab`, branch `main`.
- Read the M11 master prompt and audit criteria, M10 accepted milestone audit, M09 physical-validation owner deferral, repository coordination/audit policy and index, milestone-batch protocol, PL-0265 prompt and criteria, and mandatory PL-0264 prompt.
- Read the Design Model, mating-reference, Scan Master, viewport, and design-history contracts and implementations.
- No prompt, criteria, tracker, authority, or frozen-scope conflict was found.

## Changed files

- `core/src/packlab_core/closure_workflow.py`
- `apps/windows-studio/src/packlab_studio/closure_workflow.py`
- `tests/core/test_closure_workflow.py`
- `tests/studio/test_closure_workflow_studio.py`

No root tracker, audit verdict, prompt, criteria, dependency/lockfile, private scan, generated geometry, binary, or credential file changed.

## Implementation

- Added a deterministic PackLab Core operation that replaces only the selected CAP feature in an immutable Design Model revision. It requires the current revision and Scan Master IDs, an explicit replacement source revision derived from the current model, and an aligned mating-reference result derived from that exact replacement source and closure feature.
- Replacement checks the Scan Master digest and authority manifest, exact project/parent/scale/deferred state, neck feature identity, cap feature kinds, closure parameter bindings, and unchanged non-cap/body feature references. Stale, mismatched, review-required, or metric-verified inputs reject instead of silently retargeting.
- Builds a new Design Model revision preserving bottle body feature IDs and Scan Master binding. The Scan Master object is not modified. The output explicitly leaves physical accuracy deferred and mold, thread, seal, and manufacturing compatibility unclaimed.
- Added bounded atomic snapshot undo/redo that restore graph content by creating new immutable Design Model revisions while preserving parent binding.
- Added a Studio controller that toggles CAP viewport visibility only and delegates replacement to the Core authority. Visibility keeps the same geometry object and does not revise model geometry.
- Added Core and Studio tests for visibility, replacement revision and provenance, stale/incompatible mating rejection, undo/redo, stable body feature IDs, and UI delegation.

## Validation

Expected for material checks: exit 0; focused and predecessor regression cases and the full locked suite pass; invalid/stale mating and changed-body inputs reject; visibility leaves geometry unchanged; undo/redo create new revisions with restored graph content. Any Scan Master mutation, body-feature replacement, silent stale retarget, or physical/manufacturing compatibility claim would fail this child.

| Check | Command | Actual result |
|---|---|---|
| Focused and predecessor regression | `uv run --locked pytest -q tests/core/test_closure_workflow.py tests/studio/test_closure_workflow_studio.py tests/core/test_mating_references.py tests/core/test_design_history.py tests/studio/test_viewport.py` | Passed: 22 tests. |
| Full locked suite | `uv run --locked pytest -q` | Passed: 1,363 passed, 6 skipped, 1 deselected, 2 warnings in 37.55s. Warnings are expected duplicate-ZIP-name fixture warnings in existing tests. |
| Changed-file Ruff | `uv run --locked ruff check core/src/packlab_core/closure_workflow.py apps/windows-studio/src/packlab_studio/closure_workflow.py tests/core/test_closure_workflow.py tests/studio/test_closure_workflow_studio.py` | Passed: all checks passed. |
| Changed-file formatting | `uv run --locked ruff format --check core/src/packlab_core/closure_workflow.py apps/windows-studio/src/packlab_studio/closure_workflow.py tests/core/test_closure_workflow.py tests/studio/test_closure_workflow_studio.py` | Passed: all four files already formatted. |
| Targeted mypy | `uv run --locked mypy --follow-imports=silent core/src/packlab_core/closure_workflow.py apps/windows-studio/src/packlab_studio/closure_workflow.py` | Passed: no issues found in 2 source files. |
| Compile | `uv run --locked python -m compileall -q core/src/packlab_core/closure_workflow.py apps/windows-studio/src/packlab_studio/closure_workflow.py` | Passed: exit 0. |
| Patch whitespace | `git diff --check`; `git diff --cached --check` | Passed: no whitespace errors. |
| Secret scan | `rg -n 'api[_-]?key|token|password|secret|private[_-]?key|AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}'` over the four changed files | No matches. |
| Scope/dependency/privacy/binary review | Staged path review and dependency/lockfile review | Only the four listed source/test files changed. No dependency, private evidence, generated geometry, or binary was introduced. |
| Remote implementation visibility | `git ls-remote origin refs/heads/main` | Returned the implementation SHA above. |

An initial focused test collection found a duplicate pytest module name between Core and Studio tests. The Studio file was renamed to `test_closure_workflow_studio.py`; no test logic had run in that collection. The next focused run found two fixture issues, which were corrected. Final focused, predecessor, full suite, lint, format, type, compile, whitespace, and remote checks passed.

## Limitations and handoff

- Visibility is viewport presentation state and is not persisted as parametric geometry.
- Geometric mating references do not establish thread fit, closure compatibility, sealing, or manufacturing alignment. Physical validation remains deferred and metric state remains unverified.
- Undo/redo preserve parent binding and create revisions but do not claim physical accuracy or an owner-accepted design result.
- No ChatGPT audit artifact was created and no acceptance verdict is claimed.

READY_FOR_INDEPENDENT_AUDIT
