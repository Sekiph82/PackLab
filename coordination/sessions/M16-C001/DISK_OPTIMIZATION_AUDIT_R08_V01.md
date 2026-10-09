# M16-C001-R08 Disk-Optimization Audit V01

## Scope and method

Inspected Python tests for filesystem duplication and large-file generation with targeted searches for `copytree`, `shutil.copy*`, repository/environment/runtime copying, `write_bytes`, truncation, sparse-file creation, and `tmp_path` use. Ran the focused OWNER DEV launcher contract group through the new monitored pytest wrapper.

## Largest observed temporary producers

| Producer | Temporary data observed | Duplication finding | Action |
| --- | ---: | --- | --- |
| `tests/ci/test_owner_dev_launcher_contract.py::test_native_launcher_build_and_runtime_failure_paths` | The combined focused hygiene + launcher group had a measured basetemp peak of 427,556 bytes, largest test fixture of 397,825 bytes, and selected disposable-root peak of 450,142 bytes (wrapper run `run-20261009T181914-b1c27311`). | Builds a few small C# launcher/child fixtures, copies the PackLab icon, and creates a minimal runtime-shaped fixture. It does not copy the repository, `.venv`, package cache, or a real OWNER DEV runtime. | Kept the fixture minimal; wrapper removed 427,698 bytes at handoff. |
| `tests/ci/test_owner_dev_launcher_contract.py::test_failed_locked_sync_preserves_previous_runtime` | No separate per-test peak was recorded; its fixture is a temporary Git repository with a handful of synthetic files and one sentinel. | Does not copy PackLab source or an installed environment. | No duplication refactor needed. |
| `tests/ci/test_owner_dev_launcher_contract.py::test_compatibility_current_runtime_switch_preserves_releases` | No separate per-test peak was recorded; two tiny manifest/lock fixtures and a sentinel. | Does not copy PackLab source or an installed environment. | No duplication refactor needed. |

The search found no test that recursively copies the full repository, `.venv`, OWNER DEV runtime, or package cache. The only `shutil.copyfile` calls in tests copy freshly compiled small launcher fixtures into synthetic runtime paths. The `copytree(pywrap_source, ...)` occurrence is a static assertion about the hosted build script, not a test-time directory copy.

## Optimization and enforcement

- Added a checked-in wrapper that creates one unique `--basetemp`, polls its live size, terminates the pytest process tree above 4 GiB, reports the largest temporary entries, preserves compact diagnostics, and cleans the run directory in `finally`.
- Added an allowlisted inventory/preflight/post-test/post-task helper with dry-run deletion, ownership-marker checks, active-process checks, C: floor enforcement, optional JSON summary, and guarded `uv cache prune`.
- Focused wrapper validation: 9 passed; live basetemp peak 427,556 bytes; largest fixture 397,825 bytes; selected disposable-root peak 450,142 bytes; post-test cleanup removed the run directory.
- The full suite has not yet been run under this new monitor, so no full-suite peak is claimed. The 4 GiB monitor is the hard stop for that measurement.

## Limits

The search was static plus one focused test group, not an instrumented full-suite profile. Local and AppData OWNER DEV runtime footprint is inventoried separately because current and previous-good runtimes are protected from generic pytest cleanup.
