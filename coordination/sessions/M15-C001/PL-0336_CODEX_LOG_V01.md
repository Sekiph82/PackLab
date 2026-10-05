# PL-0336 - Codex Implementation Log V01

Cycle: `M15-C001`
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0336_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M15-C001/PL-0336_CHATGPT_AUDIT_CRITERIA_V01.md

## Synchronization and authorization

- Live `origin/main:TASKS.md` authorizes the ordered M15-C001 PL-0332 through PL-0346 batch with Required Actor CODEX. M16 remains unauthorized; `TASKS.md` was not edited.
- Read the PL-0336 prompt and criteria plus the PL-0335 predecessor prompt/criteria. M15 master scope, M14/M13 audits, M09 physical-validation deferral, ADR-0005, and coordination governance remained the verified baseline.
- Child started at synchronized `origin/main` `250dcc17d1ddcc951a1e61a235cf64c501fd2922`, divergence `0 0`, in the clean managed worktree. The dirty owner desktop checkout remains preserved.

## Implementation

Added immutable Packaging SKU revisions with stable SKU ID, bounded display name, lifecycle status, exact Packaging Asset ID/revision, optional exact Design Model link, and zero-or-more complete Label Zone/artwork/mapping/assignment references. SKU serialization contains IDs and digests only; geometry and artwork bytes are not copied. Exact source-link creation checks matching immutable M14 zone, artwork, mapping and assignment values, including the artwork digest and placement revision.

Added a bounded deterministic catalog with immutable revision history, current revision pointers, active SKU lookup by geometry, historical lookup, stale/missing target rejection, duplicate rejection, and a guard against changing a SKU's stable Packaging Asset identity. No physical fit, manufacturing or certification authority is inferred.

Files changed:

- `core/src/packlab_core/packaging_sku_library.py`
- `tests/core/test_packaging_sku_library.py`

Implementation commit: `371df09252c666f0d2f18b6d3f92ec84234b95cb`.

## Validation evidence

| Command | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest tests/core/test_packaging_sku_library.py -q` | New SKU history, geometry sharing, artwork separation and invalid-reference tests pass. | `4 passed in 0.84s`. |
| `uv run --locked pytest tests/core/test_packaging_sku_library.py tests/core/test_packaging_asset.py tests/core/test_label_zone_placement.py tests/core/test_label_artwork.py -q` | SKU and linked predecessor tests pass. | `82 passed in 1.05s`. |
| `uv run --locked pytest -q` | Locked full repository suite passes; any failure blocks this child. | `1925 passed, 11 skipped, 1 deselected, 2 warnings in 182.29s`. The warnings are existing duplicate ZIP fixture names in PackScan/transfer tests. |
| `uv run --locked ruff check core/src/packlab_core/packaging_sku_library.py tests/core/test_packaging_sku_library.py` | No changed-file lint findings. | `All checks passed!` |
| `uv run --locked ruff format --check core/src/packlab_core/packaging_sku_library.py tests/core/test_packaging_sku_library.py` | Changed files already formatted. | `2 files already formatted`. |
| `uv run --locked mypy --follow-imports=skip core/src/packlab_core/packaging_sku_library.py` | Check the changed module without surfacing unrelated imported-module failures. | `Success: no issues found in 1 source file`. |
| `uv run --locked mypy core/src/packlab_core/packaging_sku_library.py` | Normal targeted type check. | Reports two existing errors in `core/src/packlab_core/calibration/marker_detection.py` lines 112 and 140 (`len(Any | None)` and indexing `Any | None`); no diagnostic points to the new module. |
| `uv run --locked python -m compileall -q core/src/packlab_core/packaging_sku_library.py tests/core/test_packaging_sku_library.py` | Changed source and tests compile. | Exit `0`. |
| `git diff --check` and staged `git diff --cached --check` | No whitespace errors. | Passed before implementation publication. |

Tests cover two active SKUs sharing the same exact Packaging Asset revision while preserving distinct artwork revisions and SHA-256 digests; deterministic history and lookup; stale/missing geometry or artwork targets; malformed/incomplete and duplicate presentation references; duplicate SKU revision rejection; and geometry identity-change rejection. Serialized records assert no embedded SVG bytes and explicit no-copy flags.

## Scope, privacy and limitations

- The implementation commit contains only the new SKU contract and focused tests. No dependencies, lockfiles, `TASKS.md`, or governance/audit files changed.
- Canonical SKU records store stable identifiers, revision IDs, and content digests; they do not store project-root paths, local paths, source artwork bytes, geometry bytes, or private supplier files. No secrets, network behavior, physical validation, mold authorization, fit certification, or manufacturing suitability claims were introduced.
- Normal targeted mypy remains limited by the two unrelated pre-existing errors listed above; the changed module passes with imported dependencies skipped. Physical/mold validation for M09 PL-0220 through PL-0224 remains `DEFERRED_OWNER_VALIDATION`.
- A direct `python -m pytest` invocation outside the locked project environment could not import `packlab_core`; the project-standard `uv run --locked` commands above passed. An initial focused assertion typo was corrected before the final runs.

## Publication

- Implementation commit was pushed to `origin/main`: `250dcc17d1ddcc951a1e61a235cf64c501fd2922..371df09252c666f0d2f18b6d3f92ec84234b95cb`.
- After push, local `HEAD`, fetched `origin/main`, and live `git ls-remote origin refs/heads/main` all reported `371df09252c666f0d2f18b6d3f92ec84234b95cb`; the worktree was clean.
- This log is published in its distinct log-only commit; its own SHA is intentionally not predeclared here.

READY_FOR_INDEPENDENT_AUDIT
