---
coordinationSchema: packlab-coordination/v1
artifactType: codex-log
cycleId: M16-C001
version: 01
actor: CODEX
status: READY_FOR_INDEPENDENT_AUDIT
promptPath: coordination/sessions/M16-C001/OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md
criteriaPath: coordination/sessions/M16-C001/OWNER_DEV_LAUNCHER_CHATGPT_AUDIT_CRITERIA_V01.md
startingCommit: 3242d9731018543973c47a718980b2ada9c332f9
finalCommit: 2a924f4237fe2c4e8371f2537449c42721e63535
---

# PackLab OWNER DEV Launcher Codex Log V01

## Inputs read

- Live tracker at `origin/main:TASKS.md` (read only): OWNER DEV task READY for CODEX; after builder handoff resume M16-C001-R04 at PL-0350 V03.
- Prompt: [OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md)
- Criteria: [OWNER_DEV_LAUNCHER_CHATGPT_AUDIT_CRITERIA_V01.md](https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/OWNER_DEV_LAUNCHER_CHATGPT_AUDIT_CRITERIA_V01.md)
- `coordination/README.md`, `coordination/AUDIT_POLICY.md`, `coordination/AUDIT_INDEX.md`, `coordination/CODEX_LOG_CONTRACT.md`, `coordination/CODEX_LOG_TEMPLATE.md`, and the supplied PackLab `AGENTS.md` rules.
- Existing authority/reuse reference: `core/src/packlab_core/resource_paths.py`, Studio app/shell, PyInstaller spec, root `pyproject.toml`, and current icon/runtime test seams.

## Repository synchronization

- Worktree: managed isolated PackLab worktree; owner Desktop checkout was inspected read-only and left untouched.
- Remote: `https://github.com/Sekiph82/PackLab.git`, branch `main`.
- Starting HEAD and `origin/main`: `3242d9731018543973c47a718980b2ada9c332f9`; clean, `0 ahead / 0 behind`.
- Source icon discovery used only the prompt-authorized Desktop, Downloads, and Documents folders. Exact source found at `%USERPROFILE%\Desktop\PackLab.ico`.
- Owner Desktop checkout had unrelated local changes and was not synchronized, edited, or used to build the owner runtime.

## Work performed

- Added canonical `PackLab.ico`, icon manifest, source/frozen icon resolver, stable `PackLab.Studio` Windows AppUserModelID setup before `QApplication`, and QApplication/window icons.
- Added a module entry point that records a local startup failure and shows a concise Windows error only when startup returns nonzero.
- Added stable owner launcher, tracked-source runtime deployer, deterministic Desktop/Start Menu shortcut refresher, post-Codex refresh command, production PyInstaller icon integration, and standing M16 post-refresh guidance.
- Runtime assembly reads tracked files from the exact clean `HEAD` allowlist only. It rejects private/output/cache/test/log paths and reparse points; it does not copy `.git`, local project data, ignored caches, or Codex evidence.
- Runtime is staged under LocalAppData, receives `uv sync --locked --no-install-project`, and passes a source-mode Qt window/icon smoke before swap. Failed sync/smoke leaves the previous `current` runtime in place.
- Published implementation commits: `b6558caf76851e6c7d884f0a65573bc35aafea9e`, `f5f87b1346d74b44cd0d29ac52c9aaf9eb80028b`, `c5a923a02b7e54b87ab4d640ac0fe36988bb5282`, `2bfaf46387e9ee345a10def0dabf77efa30c9792`, `aa520ceaf46cdec5fea86051892971d4fa0fbb13`, `2a924f4237fe2c4e8371f2537449c42721e63535`.

## Files changed

- Added: `apps/windows-studio/assets/branding/PackLab.ico`, `icon_manifest.json`, `apps/windows-studio/src/packlab_studio/branding.py`, `__main__.py`, `tools/dev/launch_owner_packlab.ps1`, `update_owner_dev_runtime.ps1`, `refresh_owner_packlab_shortcuts.ps1`, `post_codex_owner_dev_refresh.ps1`, `tests/studio/test_owner_dev_branding.py`, `tests/ci/test_owner_dev_launcher_contract.py`, and `coordination/sessions/M16-C001/OWNER_DEV_POST_CODEX_REFRESH_POLICY_V01.md`.
- Modified: `apps/windows-studio/src/packlab_studio/app.py`, `shell.py`, and `tools/packaging/packlab_studio.spec`.
- This log is the only file in its later log-only commit.
- Protected and unchanged: root `TASKS.md`; all ChatGPT audit verdicts; PL-0350 and R04 child trackers/logs; owner Desktop checkout and its local work.

## Requirement / validation evidence

- Canonical icon: source and repository SHA-256 both `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`; source/copy digest equality verified. The runtime manifest and both shortcuts reported the same digest.
- PowerShell syntax: Windows PowerShell parser passed for all four `tools/dev/*.ps1` scripts.
- Shortcut/path quoting: `uv run --locked pytest tests/ci/test_owner_dev_launcher_contract.py -q` exercised real `.lnk` creation in temporary known-folder overrides containing spaces, and verified target/arguments/icon/description.
- Rollback: failure-injected `uv sync` test returned nonzero and retained the pre-existing runtime sentinel; temporary staging directory was removed.
- Qt icon and AppUserModelID guards: missing icon fallback did not crash; mocked Windows identity call used `PackLab.Studio`; actual Windows source-mode QApplication/window icon tests passed.
- Production packaging: focused test asserted canonical ICO is included as runtime data and set as PyInstaller EXE icon.
- Python quality: Ruff check and format, focused mypy, and `compileall` passed on changed Python files.
- Focused suite: `uv run --locked pytest tests/studio/test_owner_dev_branding.py tests/ci/test_owner_dev_launcher_contract.py tests/studio/test_shell.py -q` -> `12 passed` (final targeted rerun after last script edits: branding/launcher contract `10 passed`).
- Full locked suite on final product state: `uv run --locked pytest -q` -> `2012 passed, 11 skipped, 1 deselected`; two expected duplicate-ZIP fixture warnings in negative tests.
- `git diff --check` and staged diff checks passed. Protected `TASKS.md` diff was empty.

## Owner-machine delivery

- Stable root: `%LOCALAPPDATA%\PackLab\OwnerDev\current`.
- Final deployed source SHA at refresh: `2a924f4237fe2c4e8371f2537449c42721e63535` (published and equal to fetched `origin/main` when refreshed).
- Runtime manifest: Studio `0.1.0`, Python `3.12.10`, canonical icon digest above, `smoke_status=PASS`.
- Desktop shortcut: `%USERPROFILE%\Desktop\PackLab.lnk`.
- Start Menu shortcut: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\PackLab\PackLab.lnk`.
- Both shortcuts target Windows PowerShell with the stable LocalAppData launcher argument; Start In, icon path/hash, and description `PackLab Studio OWNER DEV • 2a924f42` were verified.
- Double-click-equivalent evidence: Windows Shell `open` verb on Desktop `PackLab.lnk` launched PackLab Studio. The visible window title was `PackLab Studio`; `WM_GETICON/ICON_SMALL2` returned a nonzero icon handle; process was `pythonw` with no console window. The window was closed after verification.
- Start Menu shell verbs did not expose `Pin to taskbar` (they exposed `Pin to Start`); recorded `TASKBAR_PIN_OS_RESTRICTED`. No registry/taskbar database edits or Explorer restart were used.
- Shell COM inspection emitted an unrelated Google Drive filesystem-pipe unavailable warning; shortcut opening and all assertions still succeeded.

## Failures encountered and fixes

- First published runtime attempt used the default editable project install from a temporary path. After swap, its editable import target still named the old stage path, so shortcut startup produced no Studio window. Changed deployment to `uv sync --locked --no-install-project` and made the launcher load source modules from the stable runtime root. The failed refresh did not authorize source edits outside scope.
- The next source smoke used relative module paths and failed with `ModuleNotFoundError`; the prior `current` remained unchanged because failure occurred before swap. Smoke now receives explicit staged source paths; launcher paths are derived from `%LOCALAPPDATA%`.
- An initial test filtered only for the venv Python path and missed Windows Python’s resolved `pythonw.exe` process. Final verification used the Shell `open` verb and found the actual titled `pythonw` window with a nonzero icon handle.
- No unresolved implementation test failures remain. The taskbar pin verb is unavailable in this Windows shell context and is recorded as an OS restriction.

## Security / privacy and scope check

- Secrets, credentials, signing material, private Kenya scans, supplier files, owner projects, ignored caches, `.git`, tests, and Codex logs were not copied into or committed with the runtime.
- Canonical files contain no user-specific absolute paths. Owner evidence paths in this log use environment variables.
- `TASKS.md` and ChatGPT audit files were not edited. No future PL implementation was included in this owner task.

## Commit and push evidence

- Implementation head: `2a924f4237fe2c4e8371f2537449c42721e63535`.
- At implementation handoff, fresh `git fetch origin main`, local HEAD, `origin/main`, and `git ls-remote origin refs/heads/main` all matched; worktree was clean.
- The required separate log-only commit follows; its own future commit SHA is intentionally not predeclared here.

## Handoff

**READY_FOR_INDEPENDENT_AUDIT**
