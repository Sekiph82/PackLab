# PL-0276 Codex Implementation Log V01

Task: **Define assembly graph for body, closure, trigger/pump and dip tube**

Cycle: `M12-C001`
Prompt: `coordination/sessions/M12-C001/PL-0276_CODEX_PROMPT_V01.md`
Criteria: `coordination/sessions/M12-C001/PL-0276_CHATGPT_AUDIT_CRITERIA_V01.md`

## Synchronization and commits

- Starting synchronized SHA: `8f3b6d0f6b0c781bf6470edda7a5d1ee1d87d847`.
- The clean detached M12 execution worktree matched `origin/main` before implementation; the Desktop owner checkout was preserved and not modified.
- Implementation commit: `d8d43e252982dc4772ef4fdcf885d8cdff34ab61`.
- `git fetch origin main` reported local `1` ahead / `0` behind. `git push origin HEAD:main` succeeded as a fast-forward; `git ls-remote origin refs/heads/main` returned `d8d43e252982dc4772ef4fdcf885d8cdff34ab61`.
- This child log is published in a separate log-only commit after implementation/evidence.

## Authorization and pre-reads

- Re-read live root `TASKS.md`, M12 master and R01 continuation work orders, PL-0276 V01 prompt/criteria, accepted M11 audit, and M09 physical-validation deferral. The ordered batch authorizes continuation through PL-0288. No task tracker or audit file was changed.
- Read `core/src/packlab_core/design_model.py`, `core/src/packlab_core/assembly_export_preview.py`, and `core/src/packlab_core/mating_references.py` in full. The new graph preserves exact Design Model and captured-parent pins; it does not repurpose the existing bottle/closure export-preview interface or claim that role references prove mating compatibility.
- Frozen scope implemented: immutable versioned metadata assembly graph for body, closure, trigger/pump, and dip tube, with stable feature references and explicit pairwise role relationships. It rejects duplicate/missing roles, stale model revisions/features, wrong feature kinds, cross-project components, and incompatible scale state/coordinate units.

## Changed files

- `core/src/packlab_core/assembly_graph.py`
- `core/src/packlab_core/design_model.py` (adds `TRIGGER_PUMP` and `DIP_TUBE` feature kinds for stable role references)
- `tests/core/test_assembly_graph.py`

## Implementation

- Added `ParametricAssemblyGraph`, immutable role and relationship enums, component input/reference values, a deterministic constructor, and exact current-component validation.
- Every role pins its own Design Model revision ID, stable feature ID, component and feature kind, project, parent binding revision, Scan Master revision/digest, prior model revision, scale state/provenance, and coordinate unit. The constructor verifies the selected feature exists in exactly that model and matches the role's permitted feature kind.
- Every graph has three deterministic explicit references: body-to-closure, closure-to-trigger/pump, and trigger/pump-to-dip-tube. Relationships contain no placement geometry or compatibility conclusion.
- Mixed `RELATIVE` and `METRIC_UNVERIFIED` states or incompatible units reject. Each component's distinct Scan Master ancestry and scale provenance remain individually preserved; the graph does not silently retarget component/model/feature references.
- Serialization marks the graph `PARAMETRIC_ASSEMBLY_METADATA`, embeds/exports no geometry, keeps `DEFERRED_OWNER_VALIDATION`, and forbids mold authorization. No CAD/STEP backend or dependency was added.
- Synthetic tests cover all four roles, stable identity under input reordering, immutable tuple/dataclass behavior, parent preservation, missing/duplicate roles, stale component revision/feature, and mixed-scale rejection.

## Validation

Expected: all four exact roles form a deterministic immutable graph; missing/duplicate/stale/incompatible inputs reject; component ancestry is retained; no physical/manufacturing authority is added. Any unmet invariant blocks continuation.

| Check | Command | Result |
|---|---|---|
| Focused graph and predecessor regressions | `uv run --locked pytest -q tests/core/test_assembly_graph.py tests/core/test_design_model.py tests/core/test_mating_references.py tests/core/test_assembly_export_preview.py` | Passed: 25 tests. |
| Changed-file Ruff | `uv run --locked ruff check core/src/packlab_core/assembly_graph.py core/src/packlab_core/design_model.py tests/core/test_assembly_graph.py` | Passed: all checks passed. |
| Changed-file formatting | `uv run --locked ruff format --check core/src/packlab_core/assembly_graph.py core/src/packlab_core/design_model.py tests/core/test_assembly_graph.py` | Passed: all three files already formatted. |
| Targeted mypy | `uv run --locked mypy --follow-imports=silent core/src/packlab_core/assembly_graph.py core/src/packlab_core/design_model.py` | Passed: no issues found in 2 source files. |
| Compile | `uv run --locked python -m compileall -q core/src/packlab_core/assembly_graph.py core/src/packlab_core/design_model.py tests/core/test_assembly_graph.py` | Passed: exit 0. |
| Patch whitespace | `git diff --check` and staged `git diff --cached --check` | Passed: no whitespace errors. |
| Locked full suite at implementation SHA | `uv run --locked pytest -q` | Passed: 1,418 passed, 6 skipped, 1 deselected, 2 duplicate-ZIP-name fixture warnings; 45.37s. Exit code 0. |
| Secret/backend scan | `rg -n -i 'api[_-]?key|token|secret|private key|supplier|raw scan|open cascade|cadquery|freecad|\bocc\b'` over changed Python files | No matches. |
| Scope/dependency/license/privacy/generated/binary review | Reviewed exact changed paths/diff, dependency and license manifests, and test fixture provenance. | Only three listed Python files changed; no dependency/license change, private/raw scan, generated geometry, binary, later-child or M13 code. Test geometry is synthetic. |
| Remote visibility | `git fetch origin main`; `git push origin HEAD:main`; `git ls-remote origin refs/heads/main` | Passed: implementation SHA `d8d43e252982dc4772ef4fdcf885d8cdff34ab61` remotely visible. |

## Failures and fixes

- The first duplicate-role test fixture accidentally replaced the dip-tube input's role with `dip_tube`, leaving all roles unique and exercising feature-kind validation instead. The fixture was corrected to duplicate the body role; the required rejection then passed.
- An initial static pass found import ordering/unused imports, formatting, and optional timestamp-offset typing issues. Ruff formatting/import fixes and explicit UTC offset narrowing resolved them. Subsequent Ruff, format, and mypy checks passed.

## Limitations and authority

- Relationships are parametric references only; they do not compute transforms, collisions, thread/seal compatibility, fit, fluid performance, or physical fit.
- Component revisions retain independent Scan Master parents and scale provenance. The graph only permits a common project, matching scale state, and coordinate unit; all components remain `DEFERRED_OWNER_VALIDATION`.
- `mm_unverified` remains unverified; no manufacturing, mold, certification, or physical accuracy claim is made. No M13 CAD/BREP/STEP behavior is present.
- No credentials, private scan, raw points, supplier asset, or unlicensed library data were added.

READY_FOR_INDEPENDENT_AUDIT
