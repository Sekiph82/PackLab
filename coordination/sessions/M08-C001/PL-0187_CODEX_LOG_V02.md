# PL-0187 Codex Implementation Log V02

Task: **Deterministic mask post-processing**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md` at synchronized start: M08 / M08-C001 / PL-0187 V02 / READY / CODEX; PL-0186 V02 is `AUDITED_PASS`; PL-0188+ and M09 are unauthorized.
- Starting local `main`: `ac34f1801413dde291e6c6617b9af902d62817e1`.
- `git fetch origin main --prune` found the local checkout four commits behind and clean. `git merge --ff-only origin/main` safely synchronized it to `ac34f1801413dde291e6c6617b9af902d62817e1`.
- Prompt read: `coordination/sessions/M08-C001/PL-0187_CODEX_PROMPT_V02.md`.
- Criteria read: `coordination/sessions/M08-C001/PL-0187_CHATGPT_AUDIT_CRITERIA_V02.md`.
- Mandatory pre-reads read in full: `docs/implementation/PL-0184_SEGMENTATION_BACKEND_CONTRACT.md`, `docs/architecture/adr/ADR-0004-sam2.1-segmentation-backend.md`, and the architecture contract linked by PL-0184 at `docs/architecture/OPENREALITY_INTEGRATION_ARCHITECTURE.md`. No conflict was found.

## Implementation

- Pipeline: `packlab.mask-post-processing`, version `1.0.0`.
- Connectivity: 4-connected foreground components and 4-connected background regions. Diagonal pixels are separate components.
- Hole filling: fill only non-boundary-connected background components with area `<= max_hole_area`; zero disables filling.
- Small-component removal: remove 4-connected foreground components with area `<= max_component_area_to_remove`; zero disables removal.
- Edge cleanup: optional, one synchronous pixel-domain pass. Fill an interior background pixel only when exactly three of its four cardinal neighbors are foreground. Never change image-boundary pixels. No erosion, dilation, resizing, resampling, or iterative smoothing is used.
- Parameters are frozen, serialize as explicit integer/boolean values, reject booleans as integers, negatives, non-integers, and limits over 1,000,000 pixels. Area thresholds also cannot exceed the raster pixel count.
- Child identity is SHA-256 over canonical JSON containing parent artifact/revision/digest, source asset/digest/dimensions/transform, pipeline ID/version, exact parameters, and output mask digest. The full identity digest defines the child artifact ID, revision ID, and `working/masks/postprocessed/<digest>/mask.mask` asset path. Creation time is emitted as metadata and excluded from identity.
- Child provenance records the full identity inputs, foreground counts before/after, holes and hole pixels filled, components and component pixels removed, edge-notch pixels filled, connectivity, and exact operation rules. Parent provenance, prompt, transform semantics, confidence, and existing quality flags are retained. The parent mask/raster is never mutated.
- `MaskArtifact` gained optional processing evidence. It is immutable and serialized only when present, preserving the existing serialized shape for raw artifacts. No dependency or lockfile change was made.

## Changed files

- `core/src/packlab_core/mask_postprocessing.py`
- `core/src/packlab_core/segmentation.py`
- `tests/core/test_mask_postprocessing.py`

No `TASKS.md`, owner ADR, audit/criteria, accepted PL-0186 evidence, lockfile, runtime/model/checkpoint, private scan, signing material, or later-task file was changed.

## Validation

- Focused processor and PL-0184/PL-0186 regressions: `uv run --locked pytest -q tests/core/test_mask_postprocessing.py tests/core/test_segmentation.py tests/core/test_sam21_backend.py` — **37 passed**.
- Exact locked full suite: `uv run --locked pytest -q` — **859 passed, 6 skipped, 1 deselected, 2 warnings**. The two warnings are existing duplicate ZIP-entry warnings from PackScan/transfer validation tests.
- Changed-file Ruff: `uv run --locked ruff check core/src/packlab_core/segmentation.py core/src/packlab_core/mask_postprocessing.py tests/core/test_mask_postprocessing.py` — **passed**.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/segmentation.py core/src/packlab_core/mask_postprocessing.py tests/core/test_mask_postprocessing.py` — **passed**.
- Targeted mypy: `uv run --locked mypy core/src/packlab_core/segmentation.py core/src/packlab_core/mask_postprocessing.py` — **passed, 2 source files**.
- Compile: `uv run --locked python -m compileall -q core/src tests` — **passed**.
- `git diff --check` and staged `git diff --cached --check` — **passed**.
- Whole-repository Ruff check reports two existing findings in unchanged `preview/windows/packlab_preview.py` (`I001` import ordering and `F401` unused `tkinter.ttk`). Whole-repository format check reports 73 existing files needing formatting. All PL-0187 changed files pass both targeted checks; unrelated files were not reformatted.
- Dependency/license review: `pyproject.toml` and `uv.lock` are unchanged; no dependency or native binary was added.
- Privacy/secrets/signing review: changed sources and synthetic tests contain no credentials, private scan data, or signing material; a focused credential/private-data pattern scan returned no matches.
- Generated/binary review: the three changed paths are Python source/test files; no generated reconstruction media or binary assets were added.
- Source immutability coverage uses public synthetic bytes and verifies they remain byte-identical. Parent artifact serialization and raster reference remain unchanged after child creation.
- Protected-file/scope review confirmed `TASKS.md`, ADR-0004, PL-0186 audit, PL-0187 prompt/criteria, `pyproject.toml`, and `uv.lock` are unchanged.

## Publication

- Implementation commit: `af79a97ffa1a13a6816ad7e5f1f66fe5f4c8ee40` (`Implement deterministic mask post-processing`).
- Log-only commit: recorded by Git history after publication.
- Synchronized start SHA: `ac34f1801413dde291e6c6617b9af902d62817e1`.
- Before publication, `main`, `origin/main`, and live GitHub `main` all resolved to the synchronized start SHA; divergence was `0 0`.
- PL-0188+ and M09 were not started.

READY_FOR_INDEPENDENT_AUDIT
