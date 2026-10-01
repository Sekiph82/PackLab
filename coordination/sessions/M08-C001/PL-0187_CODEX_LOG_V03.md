# PL-0187 Codex Remediation Log V03

Task: **Parent raster/digest integrity remediation**
Required actor: **CODEX**
Status: **READY_FOR_INDEPENDENT_AUDIT**

## Authorization and synchronization

- Live GitHub `TASKS.md` authorizes M08 / M08-C001 / PL-0187 V03 / `CHANGES_REQUIRED` / CODEX. PL-0188+ and M09 remain unauthorized.
- Synchronized starting SHA: `4a356a0e2550759842fd9dfbdc918f3bae7fde85` on `main`; the checkout was clean and matched `origin/main` and GitHub `main` after fetch/fast-forward.
- Read the V03 prompt, V03 audit criteria, source audit V01, accepted PL-0186 audit V02, and V02 implementation log.

## Integrity correction

- Boundary: `core/src/packlab_core/mask_postprocessing.py:82`, in `post_process_mask()`.
- Immediately after confirming a parent raster is present, before raster dimension checks, pixel copying, processing helpers, child raster construction, identity/path calculation, or evidence construction, require `raster.digest == parent.mask_digest`.
- A mismatch raises `MaskPostProcessingError("parent mask raster digest does not match the declared mask_digest")`. It does not recompute the declared digest, mutate the parent, or return a child.
- The generic `MaskArtifact` contract remains unchanged. Its raster is optional in-memory adapter/test data while `mask_digest` identifies the persisted mask asset; enforcing a universal equality would change accepted general contract behavior. The PL-0187 consumer now enforces equality exactly where raster bytes become the input to derived content. Valid raw SAM outputs and valid post-processed children carry matching raster/digest values and remain accepted.
- V02 pipeline version, algorithms, connectivity, thresholds, identity scheme, and source/parent immutability are unchanged.

## Tests

- Added a mismatch regression using a syntactically valid but incorrect declared parent digest. It confirms the processor and identity helpers are not called, the call raises the clear contract error, and the parent raster/artifact remain unchanged with no child/evidence returned.
- Matching parent digest, post-processed child digest validity, and repeated child identity are covered. Existing SAM 2.1 adapter tests exercise raw model artifacts whose declared digest matches the raster.
- Focused PL-0187 plus PL-0184/PL-0186 regressions: `uv run --locked pytest -q tests/core/test_mask_postprocessing.py tests/core/test_segmentation.py tests/core/test_sam21_backend.py` — **38 passed**.
- Exact locked full suite: `uv run --locked pytest -q` — **860 passed, 6 skipped, 1 deselected, 2 warnings**. The warnings are existing duplicate ZIP-entry warnings in PackScan/transfer validation.

## Static and scope validation

- Changed-file Ruff: `uv run --locked ruff check core/src/packlab_core/segmentation.py core/src/packlab_core/mask_postprocessing.py tests/core/test_mask_postprocessing.py` — **passed**.
- Changed-file format: `uv run --locked ruff format --check core/src/packlab_core/segmentation.py core/src/packlab_core/mask_postprocessing.py tests/core/test_mask_postprocessing.py` — **passed**.
- Targeted mypy: `uv run --locked mypy core/src/packlab_core/segmentation.py core/src/packlab_core/mask_postprocessing.py` — **passed, 2 source files**.
- Compile: `uv run --locked python -m compileall -q core/src tests` — **passed**.
- `git diff --check` — **passed**.
- Whole-repository Ruff reports two unrelated findings in unchanged `preview/windows/packlab_preview.py` (`I001` import order and `F401` unused `tkinter.ttk`). Whole-repository format check reports 75 unrelated files needing formatting. The task files pass their targeted checks; unrelated files were not modified.
- Dependency/license review: no dependency, lockfile, or native binary change; `pyproject.toml` and `uv.lock` are unchanged.
- Privacy/secrets/signing review: focused credential/private-data scan returned no matches. No private scan or signing material was introduced.
- Generated/binary review: only Python source/test files changed; no generated media or binary assets were added.
- Protected-file review: `TASKS.md`, owner ADRs, source audit, prompt, criteria, accepted PL-0186 evidence, and V02 log are unchanged.

## Publication and handoff

- Synchronized start SHA: `4a356a0e2550759842fd9dfbdc918f3bae7fde85`.
- Implementation commit: `3141aa0ce8d0fc29017a1ef67f1fd92bbfe4d254` (`Bind mask post-processing to parent raster digest`).
- Log-only commit: recorded in Git history after validation.
- Residual limitation: generic `MaskArtifact` construction still permits a declared digest and optional in-memory raster to differ. PL-0187 fails closed on this mismatch before deriving any child content.
- PL-0188+ and M09 were not started.

READY_FOR_INDEPENDENT_AUDIT
