# OWNER-DEV-LAUNCHER - Codex Prompt V01

Task: **Create and permanently maintain the owner's double-click PackLab Studio launcher and Windows icon integration**
Repository: https://github.com/Sekiph82/PackLab
Branch: `main`

This is an OWNER_LOCAL developer usability task. It does **not** advance or bypass PL-0350/PL-0351 release/distribution gates and does not authorize a public installer/release.

## Owner requirement

The owner will not manually create or refresh shortcuts.

Codex must make PackLab usable by double-click and must ensure the owner-local launcher is refreshed after **every future Codex implementation change**.

The owner wants:

- PackLab icon inside the application;
- PackLab icon on Desktop shortcut;
- PackLab icon in Start Menu;
- correct PackLab taskbar/window icon while the app is running;
- one stable double-click launch surface;
- no console window;
- automatic refresh after every future Codex task/commit.

## Source icon assets

The owner supplied the canonical PackLab Windows icon set.

Search only bounded owner-local locations for the supplied files:

- `%USERPROFILE%\Desktop`
- `%USERPROFILE%\Downloads`
- `%USERPROFILE%\Documents`

Expected source candidates include:

- `PackLab.ico`
- `PackLab(1).ico`
- `PackLab_ICO_Set(1).zip`
- `PackLab_Icon_Master_1024.png`
- `PackLab_Icon_256x256.png`
- `PackLab_Icon_512x512.png`

Canonical hashes from the owner-supplied attachments:

- multi-resolution ICO SHA-256:
  `a4a655fc92796413130633703602885671f5b1a0773d045ebc79d6bd522c7fc1`
- complete icon-set ZIP SHA-256:
  `7885e609a38a1ae3992a9325f6bcd2be88a96b1df0b700b1c754ca3ac53ece3f`
- 1024 master PNG SHA-256:
  `a8b44ca07426a62b65925791fb3737e35e6bb40fe90aad268158235860672835`
- 512 PNG SHA-256:
  `7946a96a4164fc0e2c61e60a4be75ee10d8a2e56d848c9c66c5d3fc9b8fe9625`
- 256 PNG SHA-256:
  `6f63b642029a4cfcf03c5606ef7be69b216bd87a6d649a7ee2ed72418923bc7d`

Do not accept a same-named file whose digest does not match.

Prefer the exact multi-resolution ICO. It contains the required Windows icon sizes and is sufficient for EXE/shortcut/window/taskbar icon use.

If the exact icon cannot be found in those bounded locations, stop this owner-local task with `OWNER_ICON_SOURCE_NOT_FOUND`. Do not fabricate or substitute artwork.

## Repository branding assets

Once the exact source icon is found:

1. copy it into the repository as:
   `apps/windows-studio/assets/branding/PackLab.ico`
2. if the exact ZIP is available, extract its canonical PNG icon set into:
   `apps/windows-studio/assets/branding/icons/`
3. preserve exact bytes/digests;
4. add a small deterministic branding manifest containing source SHA-256, copied asset SHA-256 and logical purpose;
5. ensure production PyInstaller packaging includes the ICO/branding assets.

Do not embed absolute owner paths into canonical repository files.

## Application icon integration

Implement a PackLab-owned icon helper that works in both source/dev and frozen builds.

Before the main window is shown:

- resolve `PackLab.ico` through the existing frozen/resource-path authority;
- set QApplication window icon;
- set StudioMainWindow window icon if needed;
- on Windows, set a stable explicit AppUserModelID such as:
  `PackLab.Studio`
  before QApplication/window creation so Windows taskbar grouping/icon identity is stable.

Do not use temporary build paths.

Tests must prove missing icon falls back safely without crashing, but canonical owner-dev deployment must require the icon.

## Owner-local stable runtime

Do **not** point the Desktop shortcut at a transient Codex worktree or at a stale Desktop repository checkout.

Create a stable owner-local runtime root:

`%LOCALAPPDATA%\PackLab\OwnerDev\current`

Create a PackLab-owned deploy/update script, for example:

`tools/dev/update_owner_dev_runtime.ps1`

It must be safe to run from any clean Codex worktree.

For each refresh it must:

1. require a clean/known Git worktree or explicit published commit;
2. determine exact current `HEAD` SHA;
3. mirror the runtime-required repository files into a temporary sibling directory under `%LOCALAPPDATA%\PackLab\OwnerDev`;
4. exclude:
   - `.git`;
   - Codex/session logs;
   - owner data;
   - raw/working/derived PackLab projects;
   - tests unless needed for smoke;
   - build/dist cache;
   - secrets;
5. include at minimum:
   - `pyproject.toml`;
   - `uv.lock`;
   - `core/src`;
   - `apps/windows-studio/src`;
   - branding/runtime assets required by source mode;
6. run exact `uv sync --locked` against the temporary runtime copy;
7. run a bounded source-mode PackLab Studio smoke against that runtime;
8. atomically replace/swap `OwnerDev\current` only after sync + smoke succeed;
9. retain a small path-private `owner-dev-runtime.json` containing:
   - source commit SHA;
   - Studio version;
   - Python version;
   - icon SHA-256;
   - refresh UTC timestamp;
   - smoke status;
10. leave the previous good runtime intact on any failure.

Never overwrite or clean the owner's Desktop PackLab checkout.

## Double-click launcher

Create a stable launcher under the owner runtime/tooling model, for example:

`tools/dev/launch_owner_packlab.ps1`

The launch path must:

- resolve `%LOCALAPPDATA%\PackLab\OwnerDev\current`;
- verify the runtime manifest exists;
- launch:
  `current\.venv\Scripts\pythonw.exe`
  with the real PackLab Studio module;
- use `pythonw.exe` so no console window remains;
- use `current` as working directory;
- not modify project source on launch;
- not run a network download;
- write a small local startup-failure log under `%LOCALAPPDATA%\PackLab\OwnerDev\logs`;
- show a concise Windows message box only when launch cannot start.

## Shortcut refresher

Create:

`tools/dev/refresh_owner_packlab_shortcuts.ps1`

It must recreate, on every refresh:

### Desktop
`PackLab.lnk`

using the real Windows Desktop known-folder path.

### Start Menu
`PackLab\PackLab.lnk`

under the current user's Start Menu Programs known folder.

Both shortcuts must:

- launch the stable owner launcher, not a transient EXE/worktree;
- have Start In set appropriately;
- use the canonical repo/runtime `PackLab.ico`;
- show description:
  `PackLab Studio OWNER DEV • <short HEAD SHA>`
  so we can prove the shortcut was refreshed after each change;
- overwrite the previous PackLab owner-dev shortcut deterministically.

Verify after creation:

- shortcut exists;
- target resolves;
- arguments resolve;
- icon file exists and digest matches canonical icon;
- description contains current deployed SHA.

## Taskbar behavior

Windows 11 may deny arbitrary programmatic taskbar pinning by ordinary applications/scripts.

Do not hack the Taskband registry/database and do not restart Explorer destructively.

Required behavior:

- running PackLab window/taskbar button must show the canonical PackLab icon through QApplication/window icon + AppUserModelID;
- create a correct Start Menu PackLab shortcut suitable for Windows pinning;
- if the OS exposes a legitimate non-destructive `Pin to taskbar` shell verb for this shortcut, Codex may invoke it once and verify;
- if Windows refuses/does not expose that verb, record `TASKBAR_PIN_OS_RESTRICTED` but do not fail owner-dev launch availability.

The owner must not be asked to maintain the shortcut after future changes.

## Permanent post-change refresh policy

Add a repository script:

`tools/dev/post_codex_owner_dev_refresh.ps1`

which performs, in order:

1. update owner-dev runtime from the current published/clean HEAD;
2. refresh Desktop and Start Menu shortcuts;
3. verify shortcut SHA/icon;
4. optionally run the source-mode smoke once;
5. print one concise terminal line:
   `OWNER_DEV_READY <full_sha> <desktop_lnk> <start_menu_lnk>`

Also create a checked-in Codex-facing policy document under the existing M16 coordination/development documentation and update root `TASKS.md` only through ChatGPT-owned state (do not edit TASKS in this implementation).

**Standing execution rule after implementation:** every subsequent Codex PackLab implementation prompt must run `tools/dev/post_codex_owner_dev_refresh.ps1` as its final local owner step after published remote parity is confirmed. A failure to refresh the owner runtime/shortcuts must be recorded in that child log as an owner-local delivery failure, but must not rewrite already-valid Git history.

For the current active M16 continuation, update the relevant Codex master/continuation log template or execution guidance file, but do not change root TASKS.md.

## Production EXE icon integration

Update the production PyInstaller spec so future `PackLabStudio.exe` uses the canonical `PackLab.ico`.

This does not bypass PL-0350/PL-0351. The OWNER_DEV shortcut is the immediate manual-test route; future installer/EXE still must pass the existing redistribution and clean-install gates.

## Validation

Required:

- exact icon digest verification;
- PowerShell syntax/static validation;
- shortcut creation/inspection tests using temporary known-folder overrides where practical;
- runtime deploy atomicity/failure rollback tests;
- launcher target/path quoting tests, including spaces;
- app icon resource resolution tests;
- AppUserModelID Windows guard test;
- production spec icon assertion test;
- Ruff/format/mypy/compile for changed Python;
- focused tests;
- locked full pytest;
- `git diff --check`;
- privacy/secrets/scope checks.

On the owner's actual Windows machine, run the owner-local deploy + shortcut refresh once and verify:

- Desktop PackLab.lnk exists;
- Start Menu PackLab.lnk exists;
- double-click-equivalent launch succeeds;
- PackLab window appears with correct icon;
- runtime manifest SHA equals the published HEAD;
- no console remains open.

## Publication

Publish implementation/evidence commit(s), then publish:

`coordination/sessions/M16-C001/OWNER_DEV_LAUNCHER_CODEX_LOG_V01.md`

as a separate log-only commit.

The log must record:

- source icon file found and exact SHA;
- repo asset paths/hashes;
- owner runtime root;
- deployed HEAD SHA;
- Desktop/Start Menu shortcut paths;
- shortcut target/description/icon verification;
- taskbar pin result or OS restriction status;
- double-click-equivalent launch result;
- all test results;
- final local/origin/GitHub parity.

End exactly:

`READY_FOR_INDEPENDENT_AUDIT`

Then resume the active M16 R04 continuation at PL-0350 V03.