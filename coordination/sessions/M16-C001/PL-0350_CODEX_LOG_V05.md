# PL-0350 V05 — Codex Log

Task: final native-component redistribution evidence and unsigned installer gate

Cycle: M16-C001-R06

Disposition: stopped at the source identity/provenance gate; no clearance or installer.

## Authority and synchronization

- R06 managed worktree started at `44f6eaa147f46851986ec61d9e155d495e608614`, clean.
- Fetched `origin/main`, confirmed behind-only with no local commits, and fast-forwarded to `f92c3bd1c1ffd673a6e172711e5f90aeed30070d`.
- Confirmed live `TASKS.md` authorized M16-C001-R06, OWNER DEV repair, PL-0350 V05, and conditional PL-0351 through PL-0367 continuation. Read the V08 master prompt/criteria, PL-0350 V05 prompt/criteria, partial audit V07, PL-0350 V04 audit/log/evidence, PL-0351 amended prompt/criteria, M16 coordination/audit/milestone policies, dependency/license register, current inventory/registry/workflow, PL-0225 Open3D evidence, and OWNER DEV refresh policy.
- Root `TASKS.md` and all ChatGPT audit artifacts were left unchanged. PL-0351 and later tasks were not started.

## Integrated OWNER DEV repair

Implementation commits:

- `e3afc614e80223fdcffec605d58416555200f9d9` — stable icon, shell refresh, early child monitoring, and OWNER DEV traceback diagnostics.
- `7a6e6be4224d241c14b57f3d00ed1b306ae3043c` — corrected source-path quoting in the runtime refresh smoke after the first refresh attempt exposed a PowerShell-to-Python native argument quoting failure.

Changed files: `apps/windows-studio/src/packlab_studio/__main__.py`, `apps/windows-studio/src/packlab_studio/app.py`, `tools/dev/launch_owner_packlab.ps1`, `tools/dev/refresh_owner_packlab_shortcuts.ps1`, `tools/dev/post_codex_owner_dev_refresh.ps1`, `tools/dev/update_owner_dev_runtime.ps1`, their OWNER DEV tests, and `coordination/sessions/M16-C001/OWNER_DEV_POST_CODEX_REFRESH_POLICY_V01.md`.

The shortcut refresh now copies the canonical icon into the stable `%LOCALAPPDATA%\PackLab\OwnerDev\branding\PackLab.ico` path, checks its pinned digest, verifies Windows Shell icon extraction, recreates both shortcuts, and notifies the Shell without restarting Explorer or changing icon-cache/Taskband state. The launcher uses `Start-Process -PassThru`, monitors for eight seconds, and records early child exit code plus runtime identity and any Python startup details locally. OWNER DEV-only exception handling writes traceback context for both Python startup exceptions and import-time errors while leaving the production exception boundary unchanged.

The first runtime refresh attempt at `e3afc614` failed before application startup: PowerShell's native argument handling stripped quotes around JSON source paths passed to Python `-c`. This was the refresh harness, not a QtCore loader error. Commit `7a6e6be4` passes the source paths as Base64-encoded JSON; the fresh runtime sync and source-mode GUI smoke then passed.

After the evidence commit below, `tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit` returned `OWNER_DEV_READY` at `b30e5b0d13b9006d76cc061770d6f535304f34cd`.

Real Desktop acceptance:

- Opened the actual Desktop `PackLab.lnk` through Shell `open`.
- Window title: `PackLab Studio`.
- Continuous visible/alive interval: `15.02` seconds.
- Window icon handle: nonzero (`566102553`).
- Desktop and Start Menu shortcut `IconLocation`: stable branding ICO.
- Stable ICO SHA-256: `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`.
- Cleanup: deliberate `WM_CLOSE` after the stability proof.

The provided `QtCore` DLL/procedure error was not reproduced in this source-mode launcher test. The installed-artifact regression test remains PL-0351 and was not started because PL-0350 did not clear.

## PL-0350 V05 hosted evidence and stop

Hosted run: [37492304087](https://github.com/Sekiph82/PackLab/actions/runs/37492304087), build revision `7a6e6be4224d241c14b57f3d00ed1b306ae3043c`.

Pre-clearance artifact: [11425738670](https://github.com/Sekiph82/PackLab/actions/runs/37492304087/artifacts/11425738670), text/JSON/license evidence only, 290,305 bytes.

- `uv.lock` installation, PyInstaller production staging, approved Qt assertion, and packaged no-network `qt_studio_gui`, `qt_vector_pdf`, `ocp_cad`, and `open3d_geometry` smokes passed.
- Hosted inventory: 511 files / 531,590,047 bytes; 115 unresolved shipped-file rows; 5 unresolved components; 6 unresolved items; 5 missing source-package entries; 0 missing notice sets; 0 forbidden Qt modules; 1 external prerequisite; status `BLOCKED`; `legal_review_required=true`; `public_release_authorized=false`.
- Unresolved components: `cadquery-ocp-novtk==7.9.3.1.1`, `open3d==0.20.0`, `pyside6-addons==6.11.2`, `pyside6-essentials==6.11.2`, and `shiboken6==6.11.2`. The 115 rows are the V04 baseline distribution (79 OCP, 3 Open3D, 2 Addons, 24 Essentials, 6 Shiboken, and one aggregate executable row).
- The clearance gate failed as expected; no source archives, final compliance set, or installer were produced.

The OCP upstream source at pinned commit `d69b064a3a604ebf245b1f3b14fb54c835a3a571` bounds OCCT to 7.9.3 but resolves the conda package using `occt=7.9.3=all*`; its development environment also omits exact transitive conda build identities. The staged wheel's `DELVEWHEEL` metadata identifies tool version 1.12.1 and a repair command, not exact per-DLL source versions. Thus the retained third-party native DLLs cannot be mapped to authoritative exact versions/source packages from the available pinned build provenance. No filename-based or guessed ownership was added, and the three exact native maps were not claimed complete. This is a PL-0350 V05 hard stop under its no-guessing rule.

Detailed hosted counts, evidence file hashes, and the provenance basis are in [PL-0350_REDISTRIBUTION_EVIDENCE_V05.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/PL-0350_REDISTRIBUTION_EVIDENCE_V05.md).

## Validation

| Command/check | Expected result and failure condition | Result |
| --- | --- | --- |
| `uv lock --check` | Locked dependencies resolve without lock changes; fail on mismatch | PASS |
| `uv run --locked ruff check` on changed Python files | No lint errors; fail on any diagnostic | PASS |
| `uv run --locked ruff format --check` on changed Python files | Changed Python files already formatted | PASS |
| `uv run --locked mypy core apps tools` | No type errors; fail on any diagnostic | PASS, 224 files |
| Focused owner, redistribution, Qt surface, and workflow tests | All targeted regressions pass | PASS, 33 tests |
| `uv run --locked pytest -q` | Full suite green; fail on any failed test | PASS, 2015 passed, 11 skipped, 1 deselected; 2 existing duplicate ZIP-name warnings |
| PowerShell AST parse for the four changed owner scripts | No parse diagnostics | PASS |
| Python `compileall` for changed application files | No syntax errors | PASS |
| `git diff --check` | No whitespace errors | PASS |
| Fresh hosted Windows build and capability smoke | Build and all frozen smoke groups pass; any smoke failure stops | PASS through inventory |
| Fresh hosted redistribution clearance | Zero unresolved items required; otherwise stop | BLOCKED, 6 unresolved items |

Negative/boundary coverage includes local traceback contents/identity, stable-icon digest and shortcut construction in temporary folders with spaces, locked-sync failure preserving the prior runtime, exact inventory baseline, owner shortcut and workflow contracts. An actual early-exit child was not injected end-to-end. No private/local diagnostic log, credential, signing material, scan, or supplier artifact was added to Git or the hosted artifact.

## Publication and handoff

- OWNER DEV implementation commits and V05 hosted pre-clearance evidence commit were pushed to `origin/main`.
- The evidence document is its own commit: `b30e5b0d13b9006d76cc061770d6f535304f34cd`.
- V05 child log is published in a separate log-only commit; the R06 master log records the final handoff.
- No installer, PL-0351, PL-0352 through PL-0367, M17, PL-0368, tag, GitHub Release, signing claim, or V0.1 publication was created.

READY_FOR_INDEPENDENT_AUDIT
