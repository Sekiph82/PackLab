# PL-0349 - Codex Implementation Log V01

Task: **Windows PackLab Studio build job**  
Milestone: **M16 - CI/CD, Signing & Distribution**  
Cycle: **M16-C001-R01**

## Authorization and starting state

- Live root `TASKS.md` authorized M16-C001-R01 through PL-0367 in order. `TASKS.md` was not edited.
- Executed in managed worktree `C:\Users\sekip\.codex\worktrees\packlab-m15-c001\PackLab`; owner Desktop checkout was preserved.
- At PL-0349 start, local HEAD and `origin/main` were `3449acc929d63114da0ae4bc16c0e15e7a057ddb`; worktree was clean. Read the R01 continuation prompt/criteria, PL-0349 prompt/criteria, PL-0348 predecessor prompt/criteria and child log, M15/M14 final audits, dependency/license register, versioning policy, secrets policy, and relevant workflow/source/tests before implementation.
- PL-0349 source implementation/evidence commits were published to `main`; final implementation commit is `18abcc25dc3b66fb11ed4f93bc3dd0092c31f7d0`.

## Implementation

- Added `.github/workflows/windows-studio-build.yml`: least-privilege `contents: read`, SHA-pinned checkout/setup actions, Windows hosted runner, locked `uv` environment, one-directory production PyInstaller staging build, provenance validation, content exclusions, no-network Qt smoke, and no artifact upload/signing/release.
- The entry point is `packlab_studio.app:main` via `tools/packaging/packlab_studio_entry.py`; it does not launch the preview app. The workflow packages `schemas/` and a path-free `packlab-build-provenance.json` containing the 40-character `PACKLAB_BUILD_REVISION` and semantic Studio version. It verifies the embedded values against build inputs.
- Added the PyInstaller `6.22.3` development dependency and lock entries, including locked `pyinstaller-hooks-contrib 2026.8`. The dependency/license register records build-tool license facts and explicitly leaves bundled runtime redistribution unresolved for PL-0350.
- Added frozen-runtime resource path resolution in `core/src/packlab_core/resource_paths.py` and updated schema/resource callers in PackScan/container, calibration marker policy, calibration profile, and Studio reconstruction workspace. The Studio version panel reads embedded build revision when no environment value is present.
- Build excludes `.packscan`, `.pt`, `.pth`, `.blend`, and Blender/COLMAP/OpenMVS executable names; validates the executable and exactly one embedded provenance file. No owner data, private scan, checkpoint, external engine executable, signing secret, or token was intentionally included. The staging output is not uploaded.
- Added a build-only `--packlab-build-smoke` path that constructs, shows, processes, closes, and exits the production window without network access. Smoke diagnostics, when needed, are written only to a runner temporary file.

## Correction history

- Initial implementation `a688e02d5f0cf65caf42e95ab108b70417edf950` produced a hosted smoke failure. The first push-triggered run [37423687103](https://github.com/Sekiph82/PackLab/actions/runs/37423687103) was canceled by a queued manual run; manual run [37423722627](https://github.com/Sekiph82/PackLab/actions/runs/37423722627) failed with exit code 1.
- Diagnostic refinement `0ba3be5aeca7a6430f0fdcf29ab25a95dfde0266` made smoke exceptions available in runner-temp diagnostics. Run [37424265732](https://github.com/Sekiph82/PackLab/actions/runs/37424265732) identified `RuntimeError: libshiboken: Internal C++ object (StudioMainWindow) already deleted.` The smoke accessed `window.isVisible()` after processing close events had destroyed the C++ window.
- Final fix `18abcc25dc3b66fb11ed4f93bc3dd0092c31f7d0` removed that post-close Qt object access while retaining the accepted-close check. Fresh Windows build run [37424680100](https://github.com/Sekiph82/PackLab/actions/runs/37424680100) completed successfully: lock/install, provenance, one-directory build, no-network packaged smoke, and cleanup steps all passed; hosted job duration was 1m58s.

## Local validation

- `uv run --locked pytest -q` — **1,982 passed, 11 skipped, 1 deselected, 2 warnings in 88.40s** after the final smoke fix.
- `uv run --locked mypy core apps tools` — success, zero issues in 218 source files.
- Changed-file Ruff check — pass.
- Changed-file Ruff format check — pass.
- `uv run --locked python -m compileall -q ...` for changed Python files — pass.
- `git diff --check` — pass before implementation commit.
- Local PyInstaller frozen app launch was not verified: the owner workstation's staged PySide6 QtCore load failed with “specified procedure could not be found.” The exact packaged app smoke was verified on the hosted Windows runner instead. This local limitation is not represented as a hosted failure.

## Hosted artifact and compliance facts

- Workflow run [37424680100](https://github.com/Sekiph82/PackLab/actions/runs/37424680100) on `main`, implementation SHA `18abcc25dc3b66fb11ed4f93bc3dd0092c31f7d0`: `success`. Every named build and smoke step passed.
- Workflow is configured to write Studio version, build revision, executable path, executable byte size and SHA-256, staged file/DLL counts, total staged size, smoke result, and the PL-0350 redistribution limitation to the GitHub Actions step summary. GitHub's run log endpoint returned a transient `error connecting to results-receiver.actions.githubusercontent.com` during log retrieval, so those per-file size/hash/count values are not transcribed here.
- Workflow pins PyInstaller `6.22.3`; runner setup selects Python `3.12` and uv `0.11.26`. `uv.lock` pins the exact package artifacts, and the workflow performs `uv lock --check` plus `uv sync --locked --all-groups` before building.
- The staged directory is `build/windows-studio/PackLabStudio/` with `PackLabStudio.exe`. It is not uploaded and is not a release. PyInstaller/native runtime files, including Qt and other bundled dependencies, have not been cleared for redistribution; the PL-0350 file-level license/notice review remains a hard gate.

## Publication and handoff

- Implementation/evidence commits `a688e02d5f0cf65caf42e95ab108b70417edf950`, `0ba3be5aeca7a6430f0fdcf29ab25a95dfde0266`, and `18abcc25dc3b66fb11ed4f93bc3dd0092c31f7d0` were pushed to `main`.
- At child-log authoring, local HEAD and `origin/main` were `18abcc25dc3b66fb11ed4f93bc3dd0092c31f7d0`; GitHub Actions run 37424680100 confirmed the same implementation SHA succeeded. This child log is published in a separate log-only commit.
- No tag, GitHub Release, signing operation, uploaded CI artifact, M17 implementation, or PL-0368 work was performed. The PL-0350 redistribution gate remains unresolved and mandatory.
- This is implementer evidence only; independent audit and root project-status updates remain ChatGPT-owned.

READY_FOR_INDEPENDENT_AUDIT
