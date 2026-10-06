# PL-0350 - Codex Implementation Log V02

Task: **Windows file-level redistribution inventory + versioned installer**

Cycle: **M16-C001-R02**

Prompt: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CODEX_PROMPT_V02.md
Audit criteria: https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_CHATGPT_AUDIT_CRITERIA_V02.md

## Authorization and synchronized start

- Live `TASKS.md` explicitly authorized M16-C001-R02 / PL-0350 V02. Root `TASKS.md` was not edited.
- Managed PackLab worktree was used for execution; the owner Desktop checkout and unrelated worktrees were left untouched.
- Synchronized starting commit: `7fac33346525ca92a3949f105017bed49ebe0650`; `origin/main` matched, working tree was clean, and the owner Desktop checkout and unrelated worktrees were left untouched.
- Read the active M16 R02 master prompt/criteria, PL-0350 V02 prompt/criteria, M16 partial audit V02, PL-0350 V01 prompt/criteria/log, accepted PL-0347 V02 / PL-0348 / PL-0349 audit and implementation evidence, the Windows Studio workflow, dependency/license register, versioning/secrets policies, `pyproject.toml`, `uv.lock`, and milestone batch protocol.

## Implementation and evidence commits

- `5b933b18083763a8f281b49a420e6715dbc69bab` — added the deterministic staged-file inventory, component/license registry and pinned license texts, Windows text-only evidence and clearance-gated installer workflow, Inno Setup recipe, workflow/inventory tests, and CI tool register entries.
- `397786cac0cf276d1ebd5a27e0fc6c77e07619b9` — fixed hosted Windows license-text line endings and extensionless license collection, classified Microsoft runtime items explicitly, and retained unresolved exact Qt module/plugin review.
- Implementation/evidence files: `.gitattributes`; `.github/workflows/windows-studio-build.yml`; `docs/architecture/DEPENDENCY_LICENSE_REGISTER.md`; `tests/ci/test_windows_redistribution_inventory.py`; `tests/ci/test_windows_studio_build_workflow.py`; `tools/packaging/PackLabStudio.iss`; `tools/packaging/windows_component_license_registry.json`; `tools/packaging/windows_licenses/OCP-7.9.3.1.1/LICENSE.txt`; `tools/packaging/windows_licenses/OCCT-7.9.3/LGPL-2.1.txt`; `tools/packaging/windows_licenses/OCCT-7.9.3/OCCT-LGPL-Exception.txt`; `tools/packaging/windows_licenses/Qt-PySide6-6.11.2/LGPL-3.0-only.txt`; `tools/packaging/windows_redistribution_inventory.py`.
- Neither commit changes root `TASKS.md`, a ChatGPT audit artifact, M17 work, a Git tag, or a GitHub Release.

## Implementation summary

- Added a path-free canonical inventory using the exact hosted PyInstaller COLLECT/Analysis TOCs, staged bytes, installed distribution file metadata, PE version metadata, and build revision/Studio version. The inventory records each staged file's safe relative path, digest, byte length, category, component/version mapping, mapping evidence, PE metadata where available, license status, notice references, and unresolved reason.
- Added reviewed OCP Apache-2.0, OCCT LGPL-2.1 plus exception, and PySide LGPL-3.0 license texts with pinned upstream references and checked-in digests. OCP and OCCT remain separate components. License text checkout is pinned to LF so Windows Git conversion cannot invalidate supplemental hashes.
- Added text-only evidence uploads (JSON, notices, and license text) with one-day retention. The hosted clearance step compares the exact revision/version and requires both `unresolved_count = 0` and `CLEARED_FOR_PL0350_PACKAGING`; installer staging, final re-inventory, Inno Setup installation/build, and binary upload are all gated behind that result.
- Added a versioned unsigned Inno Setup installer recipe. Inno Setup 6.7.3 is downloaded from its official release URL and hash-verified before use. No installer was built because the actual hosted bundle did not clear.

## Validation

Commands run locally:

| Command | Expected result / failure condition | Result |
| --- | --- | --- |
| `uv lock --check` | Locked resolution unchanged; fail on lock drift | PASS |
| `uv run --locked ruff check tools/packaging/windows_redistribution_inventory.py tests/ci/test_windows_redistribution_inventory.py tests/ci/test_windows_studio_build_workflow.py` | No lint findings | PASS |
| `uv run --locked ruff format --check tools/packaging/windows_redistribution_inventory.py tests/ci/test_windows_redistribution_inventory.py tests/ci/test_windows_studio_build_workflow.py` | Changed Python files already formatted | PASS |
| `uv run --locked mypy core apps tools` | No type errors | PASS; 219 source files |
| `uv run --locked pytest tests/ci/test_windows_redistribution_inventory.py tests/ci/test_windows_studio_build_workflow.py -q` | Focused inventory and workflow contracts pass | PASS; 7 passed |
| `uv run --locked pytest -q` | Full locked suite | PASS; 1,987 passed, 11 skipped, 1 deselected, 2 existing duplicate-ZIP-name warnings |
| `uv run --locked python -m compileall -q core apps tools` | Compile checks pass | PASS |
| `git diff --check` and `git diff --cached --check` | No whitespace errors | PASS after normalizing the checked-in OCCT license's trailing horizontal whitespace and recording its checked-in digest |

Hosted Windows production evidence:

- First run [37430737624](https://github.com/Sekiph82/PackLab/actions/runs/37430737624) built and smoke-tested the application and uploaded text-only evidence. Inspection found a license digest mismatch caused by Windows line-ending conversion and missed extensionless distribution license names. These implementation defects were corrected in `397786ca...`; this first report is retained as diagnostic evidence and is superseded by the corrected run below.
- Corrected run [37431656815](https://github.com/Sekiph82/PackLab/actions/runs/37431656815), source revision `397786cac0cf276d1ebd5a27e0fc6c77e07619b9`, passed locked environment validation, production one-directory build, packaged no-network smoke, inventory generation, and text-only upload. Its expected hard clearance gate failed closed; all installer and binary upload steps were skipped.
- Exact hosted stage: Studio `0.1.0`; 283 files; 141,367,765 bytes; mapped files 283. `compliance-validation.json`: `status=BLOCKED`, `unresolved_count=55`, 196 unresolved file statuses, 7 unresolved components, 22 required notice entries, and 48 collected notice files.
- Text-only artifact: `packlab-windows-compliance-preclearance-397786cac0cf276d1ebd5a27e0fc6c77e07619b9`, artifact ID `11396764327`, 138,886 bytes, one-day retention. A privacy check confirmed 53 files (4 JSON files), no EXE/DLL/PYD/ZIP/PYZ/PKG payload, and no absolute paths in JSON evidence.
- Remaining unresolved components: `microsoft-windows-runtime`; `pyinstaller-hooks-contrib`; `pyside6`; `pyside6-addons`; `pyside6-essentials`; `shiboken6`; and `unmapped-source-component`. The actual staged set includes Microsoft API-set/VCRUNTIME/UCRT files and Qt/PySide components whose exact module/plugin and third-party license mapping remains incomplete. `pyinstaller-hooks-contrib` ships a license text but installed metadata does not identify the applicable license per hook class. Some TOC source files also remain outside exact project/runtime/distribution mappings.
- OCP/OCCT and Open3D distributions were not present in the actual stage; no local or lockfile-based assumption was used to report them as shipped. The hosted inventory and exact component summary are retained in the artifact above.
- Because unresolved items remain, PL-0350 V02 is `BATCH_STOPPED`. No installer/binary artifact was produced or uploaded, and PL-0351 through PL-0367 were not started.

## Scope, privacy, and publication

- The published implementation contains only code, workflow/configuration, documentation, tests, and text license files. No credentials, private scans, supplier files, signing material, build output, or application binaries were committed.
- The first implementation commit triggered the hosted run; after correcting the Windows-specific digest issue, the second implementation commit triggered the corrected hosted run. Both were pushed explicitly to `origin HEAD:main`.
- At the time this child log is written, `HEAD`, `origin/main`, and the GitHub `main` commit are `397786cac0cf276d1ebd5a27e0fc6c77e07619b9`, with a clean implementation working tree. The child log and master continuation updates are published separately below.
- This is implementer evidence only. Independent ChatGPT audit and any owner/legal/runtime decision remain pending. PL-0368 remains `DEFERRED_POST_M17`; M17 has not started.

READY_FOR_INDEPENDENT_AUDIT
