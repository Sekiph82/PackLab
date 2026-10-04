# PL-0289 - Codex Implementation Log V01

Task: **Benchmark/select supported Python OpenCascade binding for Windows packaging**
Cycle: **M13-C001**
Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CODEX_PROMPT_V01.md
Criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M13-C001/PL-0289_CHATGPT_AUDIT_CRITERIA_V01.md

## Authorization and synchronization

- Live GitHub `TASKS.md` at starting commit `f9e93dd8cbdfaaf788f4c36d785f5cce32be2a6b` authorized M13-C001 PL-0289 through PL-0309 / READY / CODEX. M12 audit was `AUDITED_PASS`; PL-0220 through PL-0224 remained `DEFERRED_OWNER_VALIDATION`; M14 was unauthorized.
- Canonical Desktop checkout was 0 ahead / 191 behind refreshed `origin/main` and had existing owner-local modifications/untracked files. Those files were preserved. Work ran in an isolated worktree at the live origin commit.
- Before publication, `git fetch origin main --prune` showed 0 ahead / 0 behind. Final implementation push fast-forwarded GitHub `main` from `f9e93dd8cbdfaaf788f4c36d785f5cce32be2a6b` to `69f7c83f15558f1507673bd9e680d7cc3e7ba372`; `git ls-remote origin refs/heads/main` returned that same SHA.
- Master prompt, this child prompt/criteria, `pyproject.toml`, `uv.lock`, dependency/license register, ADR-0005, M09 physical validation deferral, M12 AUDITED_PASS, and milestone batch protocol were read.

## Candidate matrix and decision

| Candidate | Windows CPython 3.12 / uv result | Capability result | Decision |
| --- | --- | --- | --- |
| `cadquery-ocp==8.0.1.0.0` | Exact cp312/win_amd64 wheel installed/imported. Pulled proxy, VTK 9.6.2, Matplotlib, NumPy, Pillow and related packages; installed distribution contents totaled about 176 MB. | BREP validity, revolve, loft, boolean cut, tessellation and STEP write/read smoke passed; module version `8.0.1.0`. | Feasible, but no-VTK option better matches PackLab and avoids the VTK/Matplotlib dependency stack. |
| `cadquery-ocp==7.9.3.1.1` | Exact cp312/win_amd64 wheel installed/imported; pulled VTK and Matplotlib stack. | Same capability smoke passed; module version `7.9.3.1`. | Feasible, superseded by selected no-VTK distribution of the same OCP/kernel generation. |
| **`cadquery-ocp-novtk==7.9.3.1.1`** | **Selected.** Installed with uv 0.11.26 under Windows x86-64 / CPython 3.12.10. Only Python dependency is `cadquery-ocp-proxy==7.9.3.1.1`. Exact lock resolution succeeds. | **PASS:** BREP validity, revolve, ordered circular-section loft, boolean cut, bounded tessellation probe, STEP write and STEP read/transfer. `OCP.__version__=7.9.3.1`; bundled `TKernel` DLL file/product versions observed as 7.9.3. | Exact pin added to `pyproject.toml` and `uv.lock`. Binding API remains for the PackLab-owned CAD adapter in PL-0290 and later children. |
| `pythonocc-core==7.9.3` via PyPI/uv | `uv pip install --dry-run` failed: no matching distribution on configured PyPI index. Conda was unavailable; upstream documents conda-forge as its Python 3.12 route. | Not reached. | Not feasible for the locked uv runtime on this host; not selected. |

No runtime package/binary auto-download was added. Static search of installed OCP/proxy Python source for `urllib`, `urlopen`, `urlretrieve`, `requests`, or `download` found no matches; OCP's DLL loading patch points only at the wheel's bundled library directory.

## Artifact, licensing, and redistribution evidence

- Selected wheel: `cadquery_ocp_novtk-7.9.3.1.1-cp312-cp312-win_amd64.whl`; 46,364,919 bytes.
- PyPI JSON SHA-256 and independently downloaded wheel SHA-256 both equal `5d22339cdaac64c396f0658de8728915acfac9b868406f0078e52f50a3c25c65`; `uv.lock` records the hash and all platform wheel hashes.
- PyPI reported upload via twine 6.2.0 without Trusted Publishing. The digest pins bytes but is not an authenticated build attestation.
- The binding source project and wheel metadata identify Apache-2.0; the selected wheel itself omits the upstream source license file. OCCT 7.9.3 is a separate bundled native library under LGPL-2.1 with the Open CASCADE exception. The wheel does not carry the OCCT license/exception texts.
- Wheel archive inventory: 70 DLLs / 64,872,176 DLL bytes. `cadquery-ocp-proxy==7.9.3.1.1` is the only Python dependency of the no-VTK wheel. The full per-DLL third-party license/notice inventory is not complete; the dependency/license register marks this HIGH LICENSE / REDISTRIBUTION ATTENTION and explicitly keeps installer/binary redistribution uncleared.
- `pyproject.toml` and `uv.lock` declare exactly one direct OpenCascade binding; proxy is transitive. No private scans, supplier files, credentials, local package caches, or generated binaries were added to Git.

## Files changed

- `pyproject.toml` — pin `cadquery-ocp-novtk==7.9.3.1.1`.
- `uv.lock` — exact wheel/build hashes and transitive proxy resolution.
- `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md` — record OCCT/binding choice, exact evidence, licensing distinction, native inventory and redistribution gate.
- `coordination/sessions/M13-C001/PL-0289_CODEX_LOG_V01.md` — this log only.

Implementation/evidence commit: `69f7c83f15558f1507673bd9e680d7cc3e7ba372`.

## Validation commands and results

| Command/check | Expected result / failure condition | Actual result |
| --- | --- | --- |
| `uv sync --locked` | Full project resolves/installs with lock unchanged; failure if selected binding cannot install in project environment. | PASS; 74 packages installed, `cadquery-ocp-novtk` and proxy pinned at 7.9.3.1.1; VTK, Matplotlib, and full `cadquery-ocp` absent from runtime. |
| `uv lock --check` | Lock matches pyproject; fail on stale or unresolved lock. | PASS. |
| Windows CPython capability smoke (inline OCP probe) | Import and actual BREP/revolve/loft/boolean/tessellation/STEP operations succeed; fail on any operation, invalid topology, missing tessellation or STEP round-trip. | PASS: BREP valid; revolve valid; loft valid; boolean cut valid; 12 mesh triangles; STEP transfer/write/read/transfer-root passed. |
| `Get-ChildItem .venv\Lib\site-packages\cadquery_ocp_novtk.libs\TKernel-*.dll | % { $_.VersionInfo | select FileVersion,ProductVersion }` | Identify actual native kernel version, not just binding package version. | PASS: both version fields report 7.9.3. |
| Selected wheel download + `Get-FileHash -Algorithm SHA256`; PyPI JSON metadata; `uv tree --locked --depth 2` | Actual wheel digest equals index digest; dependencies and native artifact footprint are recorded. | PASS; hashes match; proxy is sole Python dependency; wheel has 70 DLLs / 64,872,176 bytes. |
| `uv pip install --dry-run pythonocc-core==7.9.3` | Comparison candidate resolves from the current uv/PyPI path or is recorded unavailable. | Expected unavailable result: no matching distribution. Conda was not installed. |
| `uv run --locked pytest -q tests/core/test_design_model.py tests/core/test_design_serialization.py tests/core/test_revolved_design_model.py tests/core/test_tube_fitting.py tests/core/test_pouch_family.py tests/core/test_family_conversion.py tests/core/test_assembly_graph.py tests/core/test_dip_tube.py` | Existing Design Model/assembly predecessor regressions remain green. | PASS: 56 passed. |
| `uv run --locked pytest -q` | Locked full project suite green; fail on any regression. | PASS: 1490 passed, 6 skipped, 1 deselected; 2 duplicate-ZIP-name warnings; 53.22s. |
| `uv run --locked ruff check core/src apps/windows-studio/src tools tests` | Static lint passes. | PASS: all checks passed. |
| `uv run --locked ruff format --check core/src apps/windows-studio/src tools tests` | Format check; failure is formatting drift. | Full-tree supplemental check reported 358 existing files would be reformatted and 1 already formatted. No Python file changed in PL-0289, so changed-file Python format check is not applicable; no unrelated mass-format edits were made. |
| `uv run --locked mypy core/src/packlab_core apps/windows-studio/src/packlab_studio` | Targeted typing reports no errors in changed Python. | No Python file changed. Full-tree supplemental run reports 28 existing errors in 9 unrelated Python files; not corrected outside frozen scope. |
| `uv run --locked python -m compileall -q core/src apps/windows-studio/src tools` | Existing Python sources compile. | PASS. |
| `git diff --check` and `git diff --cached --check` | No whitespace errors. | PASS; Git emitted only CRLF conversion notices for Markdown/TOML files. |
| Changed-file/scope/privacy review | Only authorized binding pin, lock, dependency/license record and child log; no protected tracker/audit files, private evidence or secret material. | PASS. `TASKS.md`, all audit artifacts and M14 files unchanged. |
| Runtime download review | Candidate does not fetch package or native artifacts when imported. | PASS by installed OCP/proxy Python-source search; artifacts are bundled in wheel and are installed only by uv. |
| Push/remote verification | Implementation commit visible as GitHub `main`. | PASS: `69f7c83f15558f1507673bd9e680d7cc3e7ba372`. |

## Failures, fixes, limitations

- Initial exploratory version probe used a nonexistent `Standard_Version` function; replaced with Windows PE `TKernel` file/product version inspection, which returned exact OCCT 7.9.3.
- Initial tessellation smoke passed an uncast face and then tried a removed OCP 8 cast helper; corrected the probe for OCP 7.9 with `TopoDS.Face_s`, then the selected locked-environment smoke passed.
- Full-tree format and mypy checks expose existing repo-wide debt described above. No source files were changed by PL-0289; fixing unrelated files would exceed scope.
- The wheel's native DLL license inventory is incomplete and the wheel omits notices. Selection supports local PackLab development but does not authorize binary redistribution; retain the HIGH attention release gate.
- CAD/BREP remains derived from exact Design Model authority. Scan Master and Design Model are unchanged. Physical validation remains `DEFERRED_OWNER_VALIDATION`; this selection grants no accuracy, mold, manufacturing, or certification claim.

## Handoff

Implementation and evidence were published separately from this log. This child has not been self-audited and is awaiting independent ChatGPT review.

READY_FOR_INDEPENDENT_AUDIT
