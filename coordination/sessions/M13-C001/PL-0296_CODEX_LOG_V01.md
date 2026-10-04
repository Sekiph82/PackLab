# PL-0296 - Codex Implementation Log V01

Task: **Tessellate BREP back to preview mesh with controlled tolerance**

Cycle: M13-C001  
Prompt: `PL-0296_CODEX_PROMPT_V01.md`  
Criteria: `PL-0296_CHATGPT_AUDIT_CRITERIA_V01.md`

## Authorization and synchronization

- Re-read root `TASKS.md` project status: M13-C001 ordered PL-0289 through PL-0309 batch; `READY`; required actor `CODEX`; M12 is `AUDITED_PASS`; no M14 authorization.
- Re-read the M13 master, M12 audit, ADR-0005, M09 deferral, PL-0294 and PL-0295 prompts, and PL-0296 criteria.
- Starting local/origin SHA: `20a8aa642e1f10bbd0f4b4f0081d59c107115041`, synchronized and clean at child start.
- Implementation commit: `ffdffd443cc95d8d1b836cfece38c6f5f26c4aa9`.

## Files changed

- `core/src/packlab_core/cad_adapter.py`
- `core/src/packlab_core/cad_preview.py`
- `tests/core/test_cad_preview.py`

No tracker, audit, prompt, criteria, dependency, lockfile, later-child, private evidence, credential, or generated binary files were changed.

## Implementation

- Added CAD-adapter tessellation that meshes a geometry copy of the registered BREP, keeping source BREP triangulation untouched. Linear deflection, angular deflection, maximum faces, vertices and triangles are explicit and bounded; extraction fails closed on invalid geometry, kernel failure, missing triangulation or any exceeded limit.
- Added `CadPreviewMeshRevision` with serialized vertices and triangles under `PREVIEW_PROXY`, exact source BREP/Design Model/operation and parent-authority revisions, inherited scale/unit state, and `DEFERRED_OWNER_VALIDATION` / `mold_use_authorized=false`.
- Preserved conservative PL-0295 feature mapping. `MAPPED` and `MAPPED_COARSE` references identify the entire preview only at `whole_output_solid_preview` scope; ambiguous and unresolved references carry no preview triangle indices.
- Added source BREP and preview mesh AABB comparison, vertex/triangle/face counts, limits, deterministic revision identity and explicit preview/tessellation limitations. Serialization states disposable preview status and explicitly denies BREP mutation, Design Model replacement, Scan Master promotion, physical accuracy and manufacturing-suitability inference.
- Tests cover coarse/fine tolerance, repeatable vertices/triangles/revision, triangle/face/tolerance bounds, BREP bounds consistency, mapped whole-solid and ambiguous feature references, rejection of a shell-only BREP, PREVIEW_PROXY serialization, relative and `mm_unverified` propagation, no authority promotion, and source revision preservation.

## Validation evidence

| Command/check | Expected result / failure condition | Actual result |
|---|---|---|
| `uv run --locked pytest tests/core/test_cad_preview.py tests/core/test_cad_brep.py tests/core/test_cad_validation.py tests/core/test_cad_feature_map.py -q` | Tessellation and predecessor regressions pass; any failure blocks child. | PASS: 27 passed. |
| `uv run --locked pytest -q` | Locked full suite passes; any failure blocks child. | PASS: 1,541 passed, 6 skipped, 1 deselected; two existing duplicate-ZIP-name warnings. |
| `uv run --locked ruff check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_preview.py tests/core/test_cad_preview.py` | Changed-file lint passes. | PASS. |
| `uv run --locked ruff format --check core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_preview.py tests/core/test_cad_preview.py` | Changed files are formatted. | PASS. |
| `uv run --locked mypy --follow-imports=silent core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_preview.py` | Changed modules pass scoped typing. | PASS: no issues in 2 source files. |
| `uv run --locked mypy core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_preview.py` | Report changed and imported typing issues. | No diagnostics in changed modules. Two errors remain in unmodified `calibration/marker_detection.py`. |
| `uv run --locked python -m compileall -q core/src/packlab_core/cad_adapter.py core/src/packlab_core/cad_preview.py` | Changed sources compile. | PASS. |
| `uv lock --check` | Lock remains valid and unchanged. | PASS; no dependency or lockfile changes. |
| `git diff --check` and staged `git diff --cached --check` | No whitespace errors. | PASS. Git emitted only the existing CRLF conversion warning for changed PowerShell-checkout Python files. |
| Credential/privacy/scope scan | No secrets, private evidence, downloads, unrelated scope or generated binaries. | PASS for changed paths; credential-pattern scan returned no matches. `TASKS.md`, audit files, dependency selection and M14+ paths remain unchanged. |
| Remote boundary | Fetch `origin/main`; verify relationship and SHA parity after publication. | PASS: fetched at `0 ahead / 0 behind` before implementation; implementation pushed to `main`; remote `refs/heads/main` verified at `ffdffd443cc95d8d1b836cfece38c6f5f26c4aa9`. |

## Failures and fixes

- Initial focused run exposed that OCCT's Bnd_Box tuple groups minima before maxima, while preview AABBs use interleaved axis pairs. The source bounds are now normalized before comparison; the corrected bound test passes within the requested linear deflection.
- Initial shell-invalid fixture used an incorrect OCP module cast. It now extracts the shell through `TopExp_Explorer`; invalid shell rejection passes.
- A first mypy check identified an unused return-value ignore, which was removed. The final scoped typing check passes.

## Limitations

- Tessellation tolerance bounds surface approximation; it does not establish physical accuracy. The bounds diagnostic compares only axis-aligned extents.
- Current feature selectors do not identify face or vertex subsets. Supported references cover the whole output-solid preview, and shared/unsupported lineage stays ambiguous or unresolved.
- PL-0220 through PL-0224 remain `DEFERRED_OWNER_VALIDATION`. The PL-0289 HIGH native-library license/notice redistribution gate remains unresolved.

## Handoff

Implementation and this log are separate commits. This child has not been independently audited. The ordered M13 batch may continue only under the frozen master prompt and while green.

READY_FOR_INDEPENDENT_AUDIT
