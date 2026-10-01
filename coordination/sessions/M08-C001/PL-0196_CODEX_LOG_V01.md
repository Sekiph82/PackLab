# PL-0196 Codex Implementation Log V01

Task: **Calculate sparse-cloud connectivity and fragmentation indicators**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0196_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0196_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live `TASKS.md` authorizes M08 / M08-C001 / the ordered PL-0188 through PL-0201 remaining batch / READY / CODEX. PL-0195 V01 predecessor log was remotely visible and ended `READY_FOR_INDEPENDENT_AUDIT`.
- Starting synchronized SHA: `be39012ca9a28d90932129f5b2e4dded50b7f664`; branch `main`; origin `https://github.com/Sekiph82/PackLab.git`; worktree clean; local/origin/GitHub-main divergence `0 0`.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later work remains unauthorized.
- Re-read the live tracker, PL-0196 V01 prompt/criteria, master remaining-batch V02 prompt, coordination README, audit policy, batch protocol, and user-provided repository instructions. No task-state or architecture conflict was found.
- Read the PackLab sparse-mapping request/stage contracts, registered-photo ratio report, and sparse diagnostic policy. The connectivity layer does not execute COLMAP or apply a geometry acceptance policy.

## Implementation

- Added `core/src/packlab_core/sparse_connectivity.py`. Its public builder accepts a successful normalized `SparseMappingRun`, the ordered image IDs represented by graph nodes, indexed undirected edges, and an explicit immutable policy.
- The report verifies the run through PL-0195's registered-photo ratio boundary, requires graph-node count to equal registered count, and checks nodes are unique, belong to the exact request identity set, and retain request order. The graph digest includes the request digest, COLMAP stage-evidence digest, ordered node IDs, and normalized edges.
- Edge validation fails closed for malformed pair shape, booleans/noninteger/out-of-range indexes, self-edges, and duplicate or reversed duplicate edges. Node and edge counts are bounded at 100,000 and 1,000,000; only the 16 largest component sizes are returned.
- The profile reports component count, largest component and ratio, isolated-node count and ratio, mean degree, connectivity classification, and an inclusive largest-component / isolated-node threshold result. Empty graphs are observed as empty with thresholds not evaluated.
- Reports omit raw image IDs, raw edges, stdout/stderr, and output paths. They retain request/stage digests and graph identity, are deterministic, and declare `diagnostic_only_no_geometry_promotion` with acceptance `not_evaluated`. Inputs are not mutated.
- Added `tests/core/test_sparse_connectivity.py` for empty and connected graphs, disconnected components, duplicate edges, invalid/self indexes, inclusive and below-threshold cases, invalid policies, identity mismatch, failed stage, bounded component output, redaction, determinism, and non-mutation.
- No Windows Studio seam was needed. No dependency, lockfile, schema, tracker, accepted predecessor, camera pose, geometry asset, or reconstruction media changed.

## Changed files

- `core/src/packlab_core/sparse_connectivity.py`
- `tests/core/test_sparse_connectivity.py`
- `coordination/sessions/M08-C001/PL-0196_CODEX_LOG_V01.md` (separate evidence commit)

## Validation

Each command was expected to pass; any child/regression/full test, changed-file lint/format/type/compile, input integrity, privacy, or protected-scope failure would stop the batch.

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_sparse_connectivity.py` | All PL-0196 cases pass | **19 passed** |
| `uv run --locked pytest -q tests/core/test_sparse_connectivity.py tests/core/test_registered_photo_ratio.py tests/core/test_sparse_mapping.py tests/core/test_sparse_diagnostics.py tests/core/test_focal_lens_consistency.py tests/core/test_photo_duplicates.py tests/core/test_pre_reconstruction_qa.py tests/core/test_mask_postprocessing.py tests/core/test_manual_mask_correction.py tests/core/test_mask_revisions.py tests/core/test_object_mask_lifting.py` | New graph diagnostics and neighboring sparse/M08 regressions pass; any failure blocks the batch | **168 passed** |
| `uv run --locked pytest -q` | Full locked suite green; any test failure blocks the batch | **954 passed, 6 skipped, 1 deselected**; 2 existing duplicate-ZIP fixture warnings from `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py` |
| `uv run --locked ruff check core/src/packlab_core/sparse_connectivity.py tests/core/test_sparse_connectivity.py` | No changed-file lint findings | **PASS** |
| `uv run --locked ruff format --check core/src/packlab_core/sparse_connectivity.py tests/core/test_sparse_connectivity.py` | Both changed Python files formatted | **PASS** |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/sparse_connectivity.py` | No type errors | **Success: no issues found in 1 source file** |
| `uv run --locked python -m compileall -q core/src/packlab_core/sparse_connectivity.py tests/core/test_sparse_connectivity.py` | Both changed files compile | **PASS**, exit 0 |
| `git diff --check` | No whitespace errors | **PASS**, exit 0 |
| `git diff --exit-code -- TASKS.md coordination/AUDIT_POLICY.md coordination/AUDIT_INDEX.md coordination/sessions/M08-C001/PL-0196_CODEX_PROMPT_V01.md coordination/sessions/M08-C001/PL-0196_CHATGPT_AUDIT_CRITERIA_V01.md pyproject.toml uv.lock` | Protected governance/prompt/criteria and dependency files unchanged | **PASS**, exit 0 |
| `uv run --locked ruff check` | Repository-wide lint clean; findings checked against changed scope | **2 pre-existing findings** in unchanged `preview/windows/packlab_preview.py` (I001 import order, F401 unused `tkinter.ttk`) |
| `uv run --locked ruff format --check` | Repository-wide formatting clean; candidates checked against changed scope | **78 unchanged files would be reformatted; 1951 files already formatted**. Both changed Python files pass the separate format check above. |
| Credential-pattern scan over changed implementation/test/log | No credentials/private keys match | **No matches** |
| Personal path/email/RAW_CAPTURE/private `.packscan` scan over changed implementation/test/log | No private source data or personal reference matches | **No matches** |
| Dependency/license review (`git diff --exit-code -- pyproject.toml uv.lock`) and generated/binary/scope review (`git status --short`; changed files limited to `.py` and `.md`) | No unreviewed dependency/license change, generated media, binary, or out-of-scope file | **PASS**; no dependency change; compile caches ignored; only two source files and this log in scope |

No native COLMAP binary, physical capture, or printer verification was run. Tests use synthetic stage summaries and synthetic graph edges. This child does not parse a COLMAP sparse model or establish how a producer extracted registered image IDs and co-visibility edges; the caller must supply the complete registered-node list and edges from the same COLMAP stage. The report binds those supplied graph identities to the request/stage digests, and does not claim native extraction, geometry quality, or physical acceptance. PL-0068 remains the existing owner gate.

## Scope, privacy, and dependency review

- Implementation and test changes are limited to the two listed Python files. `TASKS.md`, audit/prompt/criteria files, accepted predecessor code, and M09 paths were not edited.
- The builder does not mutate the normalized run, registered-image ID sequence, or edge sequence. Output includes only digests and bounded graph summaries; no raw stage text, identity paths, or edges are serialized.
- No runtime/test dependency, model, checkpoint, hosted API, private capture, signing material, generated raster, binary, mesh cleanup, or geometry-promotion artifact was added.

## Publication

- Implementation commit: `f17ba846a5c0217e8f202cc2e70901a4acf4e272` (`PL-0196: add sparse connectivity diagnostics`), containing only the core report and tests.
- Child-log-only commit: this separate publication commit, containing only `coordination/sessions/M08-C001/PL-0196_CODEX_LOG_V01.md`; its resulting SHA is verified against `origin/main` and GitHub `main` after push.
- Push target: `origin main` only.
- After push, verify local `HEAD`, `origin/main`, and GitHub `main` match with `0 0` divergence and the remote log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

READY_FOR_INDEPENDENT_AUDIT
