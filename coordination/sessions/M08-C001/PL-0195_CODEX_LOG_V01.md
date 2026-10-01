# PL-0195 Codex Implementation Log V01

Task: **Calculate registered-photo ratio after COLMAP**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0195_CODEX_PROMPT_V01.md

Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M08-C001/PL-0195_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live `TASKS.md` authorizes M08 / M08-C001 / the ordered PL-0188 through PL-0201 remaining batch / READY / CODEX. The PL-0194 predecessor log was remotely visible and ended `READY_FOR_INDEPENDENT_AUDIT`.
- PL-0195 child work began at synchronized SHA `4f5305ad993d18376ce34f99d6a90bc8bebe564a`, with branch `main`, `origin` `https://github.com/Sekiph82/PackLab.git`, clean worktree, and local/origin/GitHub-main divergence `0 0`.
- Before the PL-0195 implementation commit, a separate predecessor log-only correction added required PL-0194 prompt/criteria URLs and was published at `d5e7d67efed3dc5818a58738a9da15a7fe493157`. It changed no PL-0195 source or tests.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later work remains unauthorized.
- Re-read the live tracker, PL-0195 V01 prompt/criteria, master remaining-batch V02 prompt, coordination README, audit policy, batch protocol, and user-provided repository instructions. No authorization or architecture conflict was found.
- Read the existing PackLab COLMAP request, stage summary, normalized run, and sparse diagnostics contracts and their tests. No new command execution path or threshold/acceptance policy was introduced.

## Implementation

- Added `core/src/packlab_core/registered_photo_ratio.py` with a deterministic report over `SparseMappingRun`. The public boundary reconstructs and revalidates the request, re-normalizes the COLMAP stage result, checks count/output agreement, and fails closed on zero/duplicate image identities, malformed summaries, or contradictory/mutated counts.
- The denominator is bound by a digest over the exact ordered request image IDs and the request digest. The report includes source revision/source and matcher digests, COLMAP engine/version, stage identity/status/exit/cancel facts, a digest of stage stdout, and a canonical stage evidence digest. Raw stdout/stderr and output asset paths are omitted.
- Successful zero, partial, and complete registrations produce an observed count and normalized ratio `registered / total`; failed/cancelled/malformed runs have no ratio. Every report sets `acceptance_status` to `not_evaluated`, so measurement remains separate from downstream acceptance.
- Added `tests/core/test_registered_photo_ratio.py` covering zero/one/partial/all registration, ordered denominator identity, empty/duplicate identities, missing and malformed stage counts, count/stage mutation, failed/cancelled stages, deterministic/redacted serialization, and non-mutation.
- No UI seam was needed. No dependency, lockfile, schema, tracker, accepted predecessor, camera pose, source image, or reconstruction media changed.

## Changed files

- `core/src/packlab_core/registered_photo_ratio.py`
- `tests/core/test_registered_photo_ratio.py`
- `coordination/sessions/M08-C001/PL-0195_CODEX_LOG_V01.md` (separate evidence commit)

## Validation

Each command below was expected to pass; any failing child/regression/full test, changed-file static check, type check, compile, integrity check, or protected-scope check would stop the batch.

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest -q tests/core/test_registered_photo_ratio.py` | All PL-0195 public-boundary cases pass | **12 passed** |
| `uv run --locked pytest -q tests/core/test_registered_photo_ratio.py tests/core/test_sparse_mapping.py tests/core/test_sparse_diagnostics.py tests/core/test_focal_lens_consistency.py tests/core/test_photo_duplicates.py tests/core/test_pre_reconstruction_qa.py tests/core/test_mask_postprocessing.py tests/core/test_manual_mask_correction.py tests/core/test_mask_revisions.py tests/core/test_object_mask_lifting.py` | New report and relevant COLMAP/M08 regressions pass; any failure blocks the batch | **149 passed** |
| `uv run --locked pytest -q` | Full locked suite green; any test failure blocks the batch | **935 passed, 6 skipped, 1 deselected**; 2 existing duplicate-ZIP fixture warnings from `tests/packscan/test_container.py` and `tests/transfer/test_validation_gate.py` |
| `uv run --locked ruff check core/src/packlab_core/registered_photo_ratio.py tests/core/test_registered_photo_ratio.py` | No changed-file lint findings | **PASS** |
| `uv run --locked ruff format --check core/src/packlab_core/registered_photo_ratio.py tests/core/test_registered_photo_ratio.py` | Both changed Python files formatted | **PASS** |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/registered_photo_ratio.py` | No type errors | **Success: no issues found in 1 source file** |
| `uv run --locked python -m compileall -q core/src/packlab_core/registered_photo_ratio.py tests/core/test_registered_photo_ratio.py` | Both changed files compile | **PASS**, exit 0 |
| `git diff --check` | No whitespace errors | **PASS**, exit 0 |
| `git diff --exit-code -- TASKS.md coordination/AUDIT_POLICY.md coordination/AUDIT_INDEX.md coordination/sessions/M08-C001/PL-0195_CODEX_PROMPT_V01.md coordination/sessions/M08-C001/PL-0195_CHATGPT_AUDIT_CRITERIA_V01.md pyproject.toml uv.lock` | Protected governance/prompt/criteria and dependency files unchanged | **PASS**, exit 0 |
| `uv run --locked ruff check` | Repository-wide lint clean; findings must be checked against changed scope | **2 pre-existing findings** in unchanged `preview/windows/packlab_preview.py` (I001 import order, F401 unused `tkinter.ttk`) |
| `uv run --locked ruff format --check` | Repository-wide formatting clean; candidates must be checked against changed scope | **78 unchanged files would be reformatted; 1948 files already formatted**. Both changed Python files pass the separate format check above. |
| Credential-pattern scan over changed implementation/test/log | No credentials/private keys match | **No matches** |
| Personal path/email/RAW_CAPTURE/private `.packscan` scan over changed implementation/test/log | No private data or source-capture reference matches | **No matches** |
| Dependency/license review (`git diff --exit-code -- pyproject.toml uv.lock`) and generated/binary/scope review (`git status --short`; changed files limited to `.py` and `.md`) | No unreviewed dependency/license change, generated media, binary, or out-of-scope file | **PASS**; no dependency changes; compile caches ignored; only the two source files and this log are in scope |

The first focused run had one assertion failure because the test searched for the substring `stdout`, which also appeared in the safe `stdout_sha256` field. The assertion was tightened to reject raw `stdout`/`stderr` JSON keys specifically; the focused, regression, and full suites then passed.

No native COLMAP binary or physical capture/printer verification was run. Tests used synthetic stage summaries only; this report does not claim native execution, geometry quality, or physical acceptance. PL-0068 remains the existing owner gate.

## Scope, privacy, and dependency review

- The implementation and test changes are limited to the two listed Python files. `TASKS.md`, audit/prompt/criteria files, accepted predecessor code, and M09 paths were not edited.
- The denominator is represented by ordered identity and request digests, not copied image bytes or raw stage logs. The service does not mutate the request or run.
- No runtime/test dependency, model, checkpoint, hosted API, private capture, signing material, generated raster, or binary artifact was added.

## Publication

- Implementation commit: `44ac35e422862ab093d877324335759f83e870bc` (`PL-0195: add provenance-bound registration ratio`), containing only the analyzer and its tests.
- Child-log-only commit: this separate publication commit, containing only `coordination/sessions/M08-C001/PL-0195_CODEX_LOG_V01.md`; its resulting SHA is verified against `origin/main` and GitHub `main` after push.
- Push target: `origin main` only.
- After push, verify local `HEAD`, `origin/main`, and GitHub `main` match with `0 0` divergence and the remote log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

READY_FOR_INDEPENDENT_AUDIT
