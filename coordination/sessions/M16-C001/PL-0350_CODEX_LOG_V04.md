# PL-0350 - Codex Log V04

Task: exact redistribution closure and unsigned audit installer

Cycle: M16-C001-R05

Status: blocked at the exact redistribution evidence gate; installer not built.

## Repository and authorization

- Starting managed-worktree commit: `759469140c17c1541ec6481ab3e01ba29069b94a`.
- Fetched `origin/main`; local was clean and behind-only by eight commits. Fast-forwarded non-destructively to authorized live main `b1d5a9665f9a9527dc69ad2351ce79ddd9448a3e` before work. Desktop owner checkout was not used or modified.
- Live `TASKS.md` authorized M16-C001-R05 / PL-0350 V04 as the current CODEX task. Root `TASKS.md` was not edited.
- Read the R05 master V06, PL-0350 V04 prompt and audit criteria, partial audit V06, PL-0350 V03 log/audit, current spec/workflow, component registry and inventory tool, dependency/license register, milestone batch protocol, and OWNER DEV refresh policy.
- Preserved the accepted PL-0347 V02 through PL-0349 V03 frontier and OWNER DEV launcher behavior. No ChatGPT audit verdict was written.

## Implementation

Implementation commit: `234c212bb0fccf7fc9e22f97ef5a643cfde594b2`

Hosted evidence commit: `11c6b86c3b934d5f794894028873305d1c441ba1`

Changed files:

- `.github/workflows/windows-studio-build.yml`
- `tools/packaging/packlab_studio.spec`
- `tools/packaging/PackLabStudio.iss`
- `tools/packaging/assert_staged_qt_surface.py`
- `tools/packaging/windows_redistribution_inventory.py`
- `tools/packaging/windows_component_license_registry.json`
- `tools/packaging/windows-runtime-prerequisite.json`
- `tools/packaging/windows_licenses/OpenSSL-3.0.16/LICENSE.txt`
- `tests/ci/test_staged_qt_surface.py`
- `tests/ci/test_windows_redistribution_inventory.py`
- `coordination/sessions/M16-C001/PL-0350_REDISTRIBUTION_EVIDENCE_V04.md`

Changes map build-generated runtime JSON to the exact revision/version; map PyInstaller `base_library.zip` to CPython; map CPython's OpenSSL 3.0.16 DLLs and Apache-2.0 evidence separately; filter root Windows API-set/UCRT/VCRuntime files and unrelated `*-x64.dll` Poppler OpenSSL copies; retain nested wheel-private runtime DLLs; add a no-download x64 VC++ prerequisite manifest and installer registry/version gate; and extend inventory validation with engineering-only gate fields and source-evidence counts.

## Validation and hosted run

Local checks:

- `uv lock --check`: PASS.
- Ruff check and format check for changed Python files: PASS.
- `uv run --locked mypy core apps tools`: PASS, 224 source files.
- Focused redistribution, Qt surface, and Windows workflow tests: 22 passed.
- Locked full suite: 2012 passed, 11 skipped, 1 deselected; 2 existing duplicate ZIP-name warnings.
- `compileall` on changed Python implementation and tests: PASS.
- `git diff --check`: PASS before each implementation/evidence commit.

Hosted exact-build evidence:

- Windows Studio Build run [37481126993](https://github.com/Sekiph82/PackLab/actions/runs/37481126993), build revision `234c212bb0fccf7fc9e22f97ef5a643cfde594b2`.
- Build, approved Qt assertion, and packaged no-network smoke passed. Smoke groups: `qt_studio_gui`, `qt_vector_pdf`, `ocp_cad`, and `open3d_geometry`.
- Fresh hosted stage: 511 files / 531,589,169 bytes.
- Root `api-ms-win-*`, root `VCRUNTIME140*.dll`, root `ucrtbase.dll`, and unrelated `libcrypto-3-x64.dll` / `libssl-3-x64.dll` counts: all zero.
- `base_library.zip`, both generated JSON records, and OpenSSL `libcrypto-3.dll` / `libssl-3.dll` have exact owner mappings and per-file digests. Hosted OpenSSL PE metadata reports 3.0.16.
- Pre-clearance text artifact [11420659070](https://github.com/Sekiph82/PackLab/actions/runs/37481126993/artifacts/11420659070), SHA-256 `a646f5db38f4cfd404e9a8985e831a4267c9d94edeaed6cb2a76473615821fd4`, 290,304 bytes, one-day retention.
- Inventory: `BLOCKED`, 115 unresolved shipped-file rows, 5 unresolved components, 6 unresolved items, 5 missing source-package evidence items, 0 missing notice sets, 0 forbidden Qt components, external prerequisite count 1, legal review required `true`, public release authorized `false`.
- Unresolved components: `cadquery-ocp-novtk==7.9.3.1.1`, `open3d==0.20.0`, `pyside6-addons==6.11.2`, `pyside6-essentials==6.11.2`, `shiboken6==6.11.2`.
- Exact OCP/OCCT third-party native mapping, Open3D static native/TBB composition, Qt/PySide module/source archives and QtPdf/PDFium notice mapping remain incomplete. Required source archives were not uploaded. Clearance correctly failed; installer and final compliance/source artifacts were not produced.
- No tag, GitHub Release, V0.1 release, signing claim, or public-release authorization was created.

The earlier hosted V03 baseline was 557 files / 542,575,818 bytes and 59 unresolved items. The new exact hosted stage removes the explicitly gated host runtime files and maps deterministic ownership gaps, but remains blocked by native/source evidence.

## User-observed loader failure and continuation stop

The two supplied screenshots show the same `QtCore` loader failure: “The specified procedure could not be found.” The hosted build smoke passes in the build environment, but it is not a clean installed-artifact test and does not close this user-observed portability issue. PL-0351 amended clean-install smoke was **not started** because PL-0350 V04 did not clear. No PL-0352 through PL-0367 child was started.

## Privacy, delivery and handoff

- Reviewed the staged/inventory scope for secrets, private scans, supplier files, signing material, and local environment payloads. No such material was added to Git or the hosted text-only artifact.
- OWNER DEV refresh after implementation commit `234c212b`: `OWNER_DEV_READY`.
- OWNER DEV refresh after evidence commit `11c6b86c`: `OWNER_DEV_READY`.
- Local/origin/GitHub parity was checked after each publication before refresh. The prior requested commits `9b2f1cb1`, `bb62ac62`, and `fc2a3b54` were already ancestors of `origin/main` and needed no push.
- Batch state: `BATCH_STOPPED_AT_PL-0350_V04`. The evidence document is `coordination/sessions/M16-C001/PL-0350_REDISTRIBUTION_EVIDENCE_V04.md`.

READY_FOR_INDEPENDENT_AUDIT
