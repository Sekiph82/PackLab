# PL-0350 V03 - Windows Redistribution Evidence Codex Log

Cycle: M16-C001-R04  
Task: PL-0350 V03 redistribution remediation against accepted PL-0349 V03 stage  
Prompt: `PL-0350_CODEX_PROMPT_V03.md`  
Audit criteria: `PL-0350_CHATGPT_AUDIT_CRITERIA_V03.md`

## Authorization and synchronization

- Live `origin/main:TASKS.md` authorized PL-0350 V03 under M16-C001-R04. The accepted PL-0349 V03 frontier was preserved. Root `TASKS.md` and all audit verdict files were not changed.
- Execution checkout: `C:\Users\sekip\.codex\worktrees\packlab-m15-c001\PackLab`. Owner Desktop checkout was not used or modified.
- Starting SHA after safe synchronization: `5cd7eefe8842945d018ca16128896c4653837f71`; `origin` was `https://github.com/Sekiph82/PackLab.git`, local was equal to `origin/main`, and the worktree was clean before implementation.
- Implementation commit: `14a8e83e05e48cc70d141c65b82978c68bf2b19c` (`PL-0350 V03 map runtime hooks and pure Python licenses`). It was pushed as `HEAD:main` after fetching and confirming `0 1` ahead/behind and no dirty files. The hosted run checked out this exact commit.

## Implemented remediation

- `windows_redistribution_inventory.py` now supports metadata-only reviewed license identifiers while retaining the exact installed distribution license file as notice evidence.
- Added exact release mappings for the staged Blinker 1.9.0 (MIT), Colorama 0.4.6 (BSD-3-Clause), ItsDangerous 2.2.0 (BSD-3-Clause), and Jinja2 3.1.6 (BSD-3-Clause) distributions. Their license files were already present in the exact staged distributions.
- Split `pyinstaller-hooks-contrib` handling by source path. GPL-2.0-or-later standard analysis hooks are no longer counted as shipped solely because they ran during Analysis. Only a `pyi_rth_*.py` source under the exact `rthooks` directory is mapped as shipped Apache-2.0 runtime-hook content. The checked-in 2026.8 package license is SHA-256 pinned to `91d0baaff00773038e72c0a1fc9d5d2d38706b7a2b9c04f34296608f931b9cd0`.
- Added bounded tests for runtime-hook path classification and metadata-only license supplements.

## Exact hosted PL-0349 V03 stage and PL-0350 result

- The exact input remains the capability-complete stage built from PL-0349 V03; no stale V02 stage was substituted.
- Hosted Windows run [37465015550](https://github.com/Sekiph82/PackLab/actions/runs/37465015550) checked out `14a8e83e05e48cc70d141c65b82978c68bf2b19c`.
- Lock/install, production one-directory build, approved Qt surface assertion, frozen Qt GUI + QtPdf + OCP/CAD + Open3D no-network smoke, and exact staging inventory all passed. Inventory was 557 files / 542,575,818 bytes.
- The text-only preclearance artifact `packlab-windows-compliance-preclearance-14a8e83e05e48cc70d141c65b82978c68bf2b19c` (artifact ID `11413813934`, 289,755 bytes) reports `BLOCKED`: 59 unresolved items, 167 unresolved shipped file rows, and 7 unresolved components. Prior exact PL-0349 V03 evidence was 64 unresolved items, 173 unresolved file rows, and 12 unresolved components.
- Remaining unresolved components are `cadquery-ocp-novtk`, `microsoft-windows-runtime`, `open3d`, `pyside6-addons`, `pyside6-essentials`, `shiboken6`, and `unmapped-source-component`.
- Remaining exact file groups include 80 OCP wheel-owned files with incomplete per-file OCCT/other-native license mapping; 46 API-set/UCRT/CPython/OpenSSL files without resolved source mapping; Qt/PySide/Addons/Shiboken module-level license/notice/source evidence; Open3D 0.20.0 native/third-party mapping; two Microsoft VCRUNTIME files; and the generated `qt-staged-surface.json` and `windows-runtime-capabilities.json` files lacking a TOC ownership mapping.
- The clearance step failed on unresolved redistribution evidence as required. All installer, final-compliance, and source-artifact steps were skipped. No installer, binary application artifact, source archive artifact, tag, GitHub Release, signing claim, or V0.1 publication was produced.

## Validation

- `uv lock --check`: PASS.
- `uv run --locked pytest tests/ci/test_windows_redistribution_inventory.py -q`: PASS, 7 passed.
- `uv run --locked ruff check tools/packaging/windows_redistribution_inventory.py tests/ci/test_windows_redistribution_inventory.py`: PASS.
- `uv run --locked ruff format --check tools/packaging/windows_redistribution_inventory.py tests/ci/test_windows_redistribution_inventory.py`: PASS.
- `uv run --locked mypy`: PASS, 222 source files.
- `uv run --locked pytest -q`: PASS, 2002 passed, 11 skipped, 1 deselected, 2 warnings.
- `uv run --locked python -m compileall -q apps core tools tests`: PASS.
- `git diff --check`, JSON parse of the component registry, and the hosted workflow contract tests in the full suite: PASS.
- Repository-wide `ruff check .` remains blocked by two unchanged findings in `preview/windows/packlab_preview.py` (`I001`, `F401`). Repository-wide `ruff format --check .` reports 438 existing files would be reformatted; changed files pass the scoped checks above. No unrelated preview or repository-wide formatting changes were made.
- The owner screenshots show the same `QtCore` missing-procedure error twice. The hosted frozen build smoke passed, but no cleared installer exists to test in PL-0351's amended isolated-install job. The screenshot executable is not cryptographically tied to this hosted stage, so no root cause is claimed.

## Stop and handoff

- PL-0350 V03 is not builder-green. Exact file-level redistribution, Qt/PySide notice/source evidence, Windows prerequisite/pruning proof, and complete OCP/Open3D native mappings are not closed. No short-lived source package artifact was uploaded before complete mapping.
- PL-0351 through PL-0367 were not started. PL-0368 remains `DEFERRED_POST_M17`; M17 was not started. The amended PL-0351 installed-artifact portability gate remains mandatory for any future cleared installer.
- Implementation/evidence is this commit; this file is published separately as a log-only commit. PL-0350 remains open for independent audit and remediation. This log does not declare legal compliance or public-release authorization.

BATCH_STOPPED_AT_PL-0350_V03
