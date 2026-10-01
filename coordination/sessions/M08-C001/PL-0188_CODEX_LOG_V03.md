# PL-0188 Codex Implementation Log V03

Task: **Add manual mask-correction UI and versioned revision handoff**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md` at synchronized start: M08 / M08-C001 / remaining batch PL-0188 through PL-0201 / READY / CODEX; PL-0187 is `AUDITED_PASS`.
- Starting synchronized SHA: `62d41db33dd4acf6cd6006784009e6251e2c3193`.
- Branch: `main`; worktree clean at start; `origin` is `https://github.com/Sekiph82/PackLab.git`; local/origin divergence was `0 0`.
- Active master prompt and criteria read: `MASTER_REMAINING_CODEX_PROMPT_V02.md` and `MASTER_REMAINING_CHATGPT_AUDIT_CRITERIA_V02.md`.
- Child prompt and criteria read: `PL-0188_CODEX_PROMPT_V03.md` and `PL-0188_CHATGPT_AUDIT_CRITERIA_V03.md`.
- Mandatory pre-reads read in full: `core/src/packlab_core/segmentation.py`, `core/src/packlab_core/mask_postprocessing.py`, `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`, `apps/windows-studio/src/packlab_studio/shell.py`, and `apps/windows-studio/src/packlab_studio/viewport.py`. No contract conflict was found.

## Implementation

- Added `ManualMaskCorrectionService.correct(parent, *, editor_id, operations, created_at, pipeline_version="1.0.0")` in `core/src/packlab_core/manual_mask_correction.py`. It has no UI dependency and requires a parent in-memory raster. Before copying or reading raster values it requires `parent.raster.digest == parent.mask_digest`; mismatch and missing raster fail closed.
- Added immutable `ManualMaskEdit(x, y, action)` operations. Coordinates must be actual integers (booleans and floats are rejected); supported actions set foreground (`paint-foreground`) or background (`erase-background`). Edits are bounded to at most 16 times the raster pixel count, must be in bounds, and are applied in submitted sequence order; the last edit to a repeated coordinate wins. A final unchanged raster is rejected as a no-op.
- `editor_id` is explicit caller input, validated as a non-empty safe ASCII label of at most 128 characters; email/account syntax and path characters are rejected. No OS, machine, environment, email, or account identity is read. The immutable correction evidence records editor, parent artifact/revision/digest, pipeline/version, and the ordered normalized edit sequence.
- Child identity is SHA-256 over canonical JSON of the parent artifact/revision/digest; source asset/digest/dimensions/transform; pipeline/version; editor; ordered operations; and output mask digest. `created_at` is explicit timezone-aware metadata and excluded from revision identity. The child preserves source identity, transform, segmentation provenance, prompt, authority class, quality flags, confidence, and prior processing evidence. It sets the parent revision and appends a manual ancestry entry. Parent and source artifacts are not rewritten.
- Added optional frozen/serialized `MaskArtifact.manual_edit_evidence`; artifacts without it retain their prior serialized shape.
- Added `MaskCorrectionView` and `MaskCanvas` in the existing Studio route stack. The view renders the mask grid, collects paint/erase clicks, supports undo/cancel, and calls the injected core service only on submit. It does not create authoritative IDs or provenance. The route remains project-gated. Tests use Qt offscreen; no claim of native human visual acceptance is made.

## Changed files

- `core/src/packlab_core/manual_mask_correction.py`
- `core/src/packlab_core/segmentation.py`
- `apps/windows-studio/src/packlab_studio/mask_correction.py`
- `apps/windows-studio/src/packlab_studio/navigation.py`
- `tests/core/test_manual_mask_correction.py`
- `tests/studio/test_navigation.py`

No `TASKS.md`, master/child criteria, owner ADR, accepted predecessor evidence, dependency/lockfile, model/runtime/checkpoint, source image, private scan, signing material, generated media, or later-task implementation changed.

## Validation

- PL-0188 focus plus PL-0186/PL-0187 regressions: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q tests/core/test_manual_mask_correction.py tests/core/test_mask_postprocessing.py tests/core/test_segmentation.py tests/core/test_sam21_backend.py tests/studio/test_navigation.py` — **51 passed**.
- Exact locked full suite: `$env:QT_QPA_PLATFORM='offscreen'; uv run --locked pytest -q` — **870 passed, 6 skipped, 1 deselected, 2 warnings**. Warnings are existing duplicate ZIP entry warnings from PackScan/transfer validation tests.
- Changed-file Ruff: `uv run --locked ruff check <six changed files>` — **passed**.
- Changed-file format: `uv run --locked ruff format --check <six changed files>` — **passed**.
- Targeted mypy with silent import following: `uv run --locked mypy --follow-imports=silent core/src/packlab_core/manual_mask_correction.py apps/windows-studio/src/packlab_studio/mask_correction.py` — **passed, 2 source files**.
- Normal targeted mypy including segmentation/navigation — **reports four existing errors in unchanged `core/src/packlab_core/packscan/container.py`** (object `.get`, int/object comparison, and two nullable path arguments). No errors were reported in the two new modules when checked with silent import following; unrelated PackScan code was not changed.
- Compile: `uv run --locked python -m compileall -q core/src apps/windows-studio/src tests` — **passed**.
- `git diff --check` and staged `git diff --cached --check` — **passed**.
- Whole-repository Ruff reports two existing findings in unchanged `preview/windows/packlab_preview.py` (import order and unused `tkinter.ttk`). Whole-repository format check reports 78 existing files needing formatting. All six changed files pass both changed-file checks; unrelated files were not altered.
- Dependency/license review: `pyproject.toml` and `uv.lock` are unchanged; no dependency, hosted service, or binary was added.
- Privacy/secrets/signing review: changed-file scan for token/private-key/password literals found no matches; editor provenance is caller-supplied and contains no ambient identity.
- Generated/binary review: additions are Python source/tests only; no generated reconstruction media or binaries were added.
- Protected-file/scope review: `TASKS.md`, owner ADRs, master log, all audit/criteria files, accepted PL-0187 files, and M09/later-task files are unchanged.

## Publication

- Implementation commit: `a334b85cb8e8f2c104d8a4d495ae01a534c2af29` (`Add deterministic manual mask correction`).
- Starting synchronized SHA: `62d41db33dd4acf6cd6006784009e6251e2c3193`.
- Implementation push: `git push origin main` succeeded. Follow-up fetch, `git rev-parse HEAD`, `git rev-parse origin/main`, and `git ls-remote origin refs/heads/main` all resolved to `a334b85cb8e8f2c104d8a4d495ae01a534c2af29`; divergence was `0 0`.
- PL-0189+ and M09 had not started at this PL-0188 child boundary. Per the active master prompt, continue to PL-0189 after this log is published and verified.

READY_FOR_INDEPENDENT_AUDIT
