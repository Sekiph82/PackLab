# PackLab local disk and test-fixture audit — V15

Cycle: `M16-C001-R08`
Authority source: `origin/main` at `9cbb3b9117bbd0609bf9214d931ccb160416d196`

## Test fixture audit

Source searches covered `tests/` for recursive copies, repository/runtime/cache copies, environment copies, clones, extraction, and temporary-tree creation. No test copies the PackLab repository, `.venv`, OWNER DEV runtime, or package cache into each test case.

Largest identified byte-producing fixtures:

| Producer | Observed source behavior | Expected bound / change |
|---|---|---|
| `tests/ci/test_owner_dev_launcher_contract.py` | Creates small synthetic runtime directories, copies one bootstrap file and generated test executables, and compiles tiny C# child stubs. | Individual files only; no complete runtime copy. The new wrapper measures each pytest test tree and stops above 2 GiB. |
| `tests/calibration/test_calibration_mats.py::_root_copy` | Copies one SVG source before test mutation. | A4 SVG is 5,199 bytes; A3 SVG is 5,208 bytes. No change needed. |
| `tests/studio/test_reconstruction_workspace.py::_packscan` | Writes a two-image synthetic PackScan fixture and small project metadata under `tmp_path`. | Targeted synthetic fixture; no repository or runtime duplication. The wrapper measures its test directory live. |
| `tests/ci/test_windows_studio_build_workflow.py` | Mentions a `copytree` of the pinned upstream `pywrap` source in a source-contract assertion. | This checks the build implementation; it does not copy anything during pytest. |

The existing suite already uses focused synthetic fixtures. No pathological full-repository/runtime copy was found to refactor. The implementation change is structural: the monitored wrapper now enforces the 4 GiB basetemp, 2 GiB individual test tree, and 8 GiB aggregate disposable PackLab limits while preserving a compact failure tail.

## Initial local measurements

- C: free space before the managed V15 worktree: `208945795072` bytes.
- C: free space at disk preflight after worktree creation: `199911841792` bytes (about 186.2 GiB; above the required 40 GiB).
- `%TEMP%\PackLab`: `0` bytes.
- `%TEMP%\pytest-of-sekip`: `0` bytes; no legacy numeric run IDs were supplied for deletion.
- Allowlisted PackLab temp/build/staging footprint at preflight: `0` bytes.
- pip cache: `995.1 MB`, below the 2 GiB reduction threshold.
- Active pytest/mypy/test processes: none at initial inventory.

## OWNER DEV and worktree retention

The active Desktop runtime manifest and launcher fingerprint identify source `9cbb3b9117bbd0609bf9214d931ccb160416d196`; the current runtime smoke status is `PASS`. The newest distinct smoke-passing previous release is `a8dcd89f624435e79683e6db3067041c94179ddf-2ed5f660d5c94e0f91985295295b4b01`. The Start Menu shortcut targets the Desktop native launcher, and its EXE digest matched the launcher fingerprint. No PackLab Studio process was running from an OWNER DEV path during the check.

The Desktop OWNER DEV inventory contained eight superseded release candidates and eight redundant rollback snapshots, each about 1.318 GB. The legacy `%LOCALAPPDATA%\PackLab\OwnerDev` tree measured `60623058044` bytes. Desktop cleanup removed `21085263026` logical bytes across the eight releases and eight rollback copies. C: free space increased from `199895486464` to `219967844352` bytes across the cleanup interval. The current Desktop runtime (`9cbb3b9117bbd0609bf9214d931ccb160416d196-1802e5f2bb004d9fb32da9b40af452f5`), one distinct previous-good release (`a8dcd89f624435e79683e6db3067041c94179ddf-2ed5f660d5c94e0f91985295295b4b01`), its verified rollback snapshot, the stable launcher, and Desktop EXE were retained.

The AppData removal did not reach a stable empty state: the exact old tree was measured and targeted, but the final inspection found `%LOCALAPPDATA%\PackLab\OwnerDev` present again with `logs` and `releases` entries. Those paths were retained for safety; no second deletion was attempted. The Desktop launcher remains independently verified as the Start Menu target.

Worktree review found no safe retirement candidate: the Desktop checkout is dirty; the R07 worktree is unpublished; the R07 timeout worktree is dirty; the V14 checkout is owned by another task; the new V15 worktree is active; and the OWNER DEV launcher checkout is unpublished. These were retained. No worktree was removed or pruned.

## Changes made

- Extended the allowlisted hygiene helper to enforce the aggregate 8 GiB limit, account for the disposable roots, retain only manifest-verified OWNER DEV identities, and remove the exact obsolete LocalAppData OWNER DEV tree only after verifying the active Desktop launcher/shortcut and process ownership.
- Extended the test wrapper to enforce the aggregate 8 GiB cap and request a graceful process-tree stop before forced termination.
- Added static contract checks and updated the local disk-hygiene instructions.

## Validation and final measurements

- Disk hygiene helper preflight: `DISK_PREFLIGHT_PASS`; free space `199911841792` bytes; disposable footprint `0` bytes.
- Monitored wrapper test: `tools/dev/run_packlab_tests.ps1 -q tests/ci/test_packlab_disk_hygiene_contract.py` — **3 passed**; peak basetemp `142` bytes; the run directory was removed in `finally`; post-test disposable footprint `0` bytes.
- Final post-test hygiene: `DISK_HYGIENE_PASS`; free space `219940741120` bytes; disposable footprint `0` bytes; pytest basetemp absent.
- uv cache prune was attempted after cleanup and again after the focused validation. Both attempts were safely skipped because active Godot AI and MCP Blender processes use executables under `%LOCALAPPDATA%\uv\cache\archive-v0`. `uv_cache_bytes_before/after=NOT_MEASURED_ACTIVE_CACHE_PROCESS`; no cache bytes were removed.
- A read-only recursive uv cache size walk was stopped after more than 15 minutes of CPU time without returning. No uv cache mutation occurred.
- The all-project `uv cache prune` gate remains incomplete until those processes stop. The active task therefore stops before PL-0350 V07 and any heavy local validation.
