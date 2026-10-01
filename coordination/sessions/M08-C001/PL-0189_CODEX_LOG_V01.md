# PL-0189 Codex Implementation Log V01

Task: **Version mask revisions independently and invalidate downstream geometry**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md` authorizes M08 / M08-C001 / the ordered PL-0188 through PL-0201 batch / READY / CODEX. PL-0188 V03 log was remotely visible before this child began.
- Starting synchronized SHA: `4f421ee43120e14777e747d81d8a2b7f4fea7beb`.
- Branch: `main`; worktree clean; `origin` is `https://github.com/Sekiph82/PackLab.git`; local/origin divergence: `0 0`.
- M07 remains `AUDITED_PASS`; PL-0068 remains `OWNER_REQUIRED`; M09/later milestone remains unauthorized.
- Active master prompt/criteria and PL-0189 V01 prompt/criteria were read. `AGENTS.md`, coordination README, audit policy/index, milestone batch protocol, `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md`, and `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md` were read. No conflict was found.

## Implementation

- Added `MaskRevisionService` in `core/src/packlab_core/mask_revisions.py`, with immutable `publish_initial` / `publish_child` snapshots, `current`, and retained `history` for each project/source revision. Child publication requires the exact current parent object, making stale or forged parent state fail closed.
- Child publication preserves all prior masks except explicitly named replacements, which remain available in the immutable parent snapshot. Additions are retained. Empty sets, duplicate artifact IDs, duplicate mask revision IDs, unknown replacement parents, stale heads, and empty child changes are rejected.
- A replacement must use a new artifact ID, bind its `parent_mask_revision` to the replaced artifact, append manual ancestry that preserves the old prefix and identifies editor/action identity, and preserve source image identity/digest/dimensions, transform, and segmentation/model provenance.
- Mask-set `revision_id` is deterministic SHA-256 over canonical project/source identity, parent revision ID/digest, and canonically sorted mask authority fields. Artifact and set creation timestamps are excluded. `MaskSetRevision.revision_digest` also excludes mask creation timestamps so identity and geometry bindings remain stable when only publication-time metadata differs. Existing serialized fields remain present.
- Added `GeometryMaskRevisionBinding` plus `require_geometry_current`. Geometry records its mask-set ID/digest; a changed current set raises `StaleMaskGeometryError` and requires regeneration. No production object-geometry type exists before PL-0190, so this public core gate is validated with synthetic revisions and is ready for the PL-0190 consumer.

## Changed files

- `core/src/packlab_core/mask_revisions.py`
- `core/src/packlab_core/segmentation.py`
- `tests/core/test_mask_revisions.py`
- `coordination/sessions/M08-C001/PL-0189_CODEX_LOG_V01.md` (separate log-only commit)

No `TASKS.md`, master log, audit/criteria artifact, owner ADR, accepted child evidence, dependency/lockfile, model/runtime/checkpoint, private source scan, RAW_CAPTURE bytes, signing material, generated reconstruction media, or later-task implementation changed.

## Validation

- Focused PL-0189 and predecessor regressions: `uv run --locked pytest -q tests/core/test_mask_revisions.py tests/core/test_manual_mask_correction.py tests/core/test_segmentation.py tests/core/test_mask_postprocessing.py tests/core/test_sam21_backend.py` — expected: all publication, identity, ancestry, duplicate/stale/error, source immutability and PL-0186/0187 regression tests pass; failure: any failed assertion or non-zero exit. Actual: **52 passed**, exit 0.
- Exact locked full suite: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q` — expected: suite completes with no failures; failure: any failed test or non-zero exit. Actual: **875 passed, 6 skipped, 1 deselected, 2 warnings**, exit 0. Existing warnings are duplicate ZIP entry fixture warnings in PackScan/transfer tests.
- Changed-file Ruff: `uv run --locked ruff check core/src/packlab_core/mask_revisions.py core/src/packlab_core/segmentation.py tests/core/test_mask_revisions.py` — expected clean; actual passed, exit 0.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/mask_revisions.py core/src/packlab_core/segmentation.py tests/core/test_mask_revisions.py` — expected already formatted; actual passed, exit 0.
- Whole-repository Ruff: `uv run --locked ruff check` — actual exit 1 for two existing findings in unchanged `preview/windows/packlab_preview.py` (import order and unused `tkinter.ttk`). No unrelated files changed.
- Whole-repository format: `uv run --locked ruff format --check` — actual exit 1; **78 files would be reformatted, 1928 files already formatted**. All PL-0189 changed source/test files pass the changed-file format check.
- Targeted mypy: `uv run --locked mypy core/src/packlab_core/mask_revisions.py core/src/packlab_core/segmentation.py` — expected no errors in the changed contract/service; actual **Success, 2 source files**, exit 0.
- Compile: `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests` — expected no syntax errors; actual passed, exit 0.
- `git diff --check` — expected no whitespace errors; actual passed, exit 0.
- Protected-file/scope review: `git diff -- TASKS.md coordination/sessions/M08-C001/MASTER_REMAINING_CODEX_LOG_V02.md` was empty; only the two authorized core files, dedicated test, and required child log changed.
- Dependency/license review: `pyproject.toml` and `uv.lock` are unchanged; no dependency, hosted service, model, or binary was added.
- Privacy/secrets/signing review: targeted credential/private-key literal scan found no matches. Test source is synthetic; no ambient identity is read.
- Generated/binary review: additions are Python source/tests/log only; no generated geometry or reconstruction media were added.
- Failures/fixes: no PL-0189 validation failures remained; the final focused and full gates passed.
- Native geometry/UI or physical acceptance was not claimed. The stale-binding test is synthetic and demonstrates the public fail-closed regeneration requirement.

## Publication

- Implementation commit: `096c428839324119b3fb159a556ebc4613f9e88d` (`Publish deterministic mask set revisions`).
- Starting synchronized SHA: `4f421ee43120e14777e747d81d8a2b7f4fea7beb`.
- Implementation push succeeded. Follow-up fetch, `git rev-parse HEAD`, `git rev-parse origin/main`, and `git ls-remote origin refs/heads/main` all resolved to `096c428839324119b3fb159a556ebc4613f9e88d`; divergence was `0 0`. The separate log-only commit follows.
- PL-0190+ and M09 had not started at this PL-0189 child boundary; after this log is published and remotely verified, continue to PL-0190 under the active master batch.

READY_FOR_INDEPENDENT_AUDIT
