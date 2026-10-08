# PackLab OWNER DEV Post-Codex Refresh Policy V01

This is the standing local-delivery procedure established by `OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md`.

## Future PackLab implementation handoff

After an implementation is committed and pushed, and local `HEAD`, `origin/main`, and GitHub `main` are confirmed
equal, the Codex implementation actor runs:

```powershell
tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit
```

The script builds a new runtime from that exact clean published commit and runs locked dependency sync plus a bounded
source-mode smoke before replacing the prior runtime. It verifies the canonical icon at
`%LOCALAPPDATA%\PackLab\OwnerDev\branding\PackLab.ico`, builds the checked-in Windows GUI launcher source with an
already-installed compiler, and embeds that exact icon in
`%LOCALAPPDATA%\PackLab\OwnerDev\launcher\PackLab.exe`. It atomically copies the verified launcher to the real
Desktop known folder as `PackLab.exe`, removes only the obsolete owner-created `PackLab.lnk` after that copy passes
hash, PE GUI-subsystem, and Shell icon checks, then recreates the Start Menu shortcut against the stable native EXE.
The launcher runs the runtime's `pythonw.exe` and bootstrap directly, without PowerShell, and monitors child startup
for ten seconds. OWNER DEV-only Python tracebacks and native launcher failures remain in the LocalAppData logs.

The post-refresh command prints `OWNER_DEV_EXE_READY <full_sha> <desktop_exe> <launcher_exe>` only after runtime SHA,
canonical icon, EXE hashes, GUI subsystem, Shell icon extraction, Desktop `.lnk` absence, and native Start Menu target
checks pass. The Desktop executable is byte-identical to the stable launcher and never captures a Codex worktree.
This owner-local source runtime does not satisfy PL-0350 redistribution or PL-0351 clean-install acceptance.

Record the command, exit status, deployed SHA, shortcut paths, and failures in the child task's own Codex log. A local
refresh failure is an owner-local delivery failure; it does not authorize rewriting published commits, modifying the
owner's Desktop checkout, or claiming independent acceptance. Never run the refresh before the task's published
remote parity is verified. The active prompt may explicitly define a different final handoff and takes precedence.

## Boundaries

- `TASKS.md` and ChatGPT audit verdicts remain ChatGPT-owned.
- The runtime is path-private under LocalAppData and contains no PackLab project data, Codex logs, tests, credentials,
  or Git metadata.
- Launch uses `pythonw.exe`, does not download or update dependencies, and does not write to repository source.
- Taskbar pinning uses only a legitimate Windows shell verb if one is exposed. Never edit Taskband registry state or
  restart Explorer to force a pin.
- This owner-dev source runtime does not satisfy PL-0350 redistribution or PL-0351 clean-install acceptance.
