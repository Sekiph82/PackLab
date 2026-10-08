# PackLab OWNER DEV Post-Codex Refresh Policy V01

This is the standing local-delivery procedure established by `OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md`.

## Future PackLab implementation handoff

After an implementation is committed and pushed, and local `HEAD`, `origin/main`, and GitHub `main` are confirmed
equal, the Codex implementation actor runs:

```powershell
tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit
```

The script builds a new immutable runtime release from that exact clean published commit under
`<Desktop>\PackLab\OwnerDev\releases\<source-commit>-<release-id>` and runs locked dependency sync plus a bounded
source-mode smoke before publishing a native launcher bound to that release. Existing releases remain in place so an
older Desktop EXE continues to resolve its matching runtime throughout the refresh. After the new native EXE is
atomically installed, the historic `current` path is updated from a staged, verified copy for diagnostics and older
OWNER DEV helpers; the new native EXE never resolves its runtime through that mutable path. It verifies the canonical icon at
`<Desktop>\PackLab\OwnerDev\branding\PackLab.ico`, builds the checked-in Windows GUI launcher source with an
already-installed compiler, and embeds that exact icon in
`<Desktop>\PackLab\OwnerDev\launcher\PackLab.exe`. It atomically copies the verified launcher to the real
Desktop known folder as `PackLab.exe`, removes only the obsolete owner-created `PackLab.lnk` after that copy passes
hash, PE GUI-subsystem, and Shell icon checks, then recreates the Start Menu shortcut against the stable native EXE.
The native EXE embeds the exact published source SHA and immutable runtime ID, verifies both against the release
manifest, then runs that release's `pythonw.exe` and bootstrap directly without PowerShell. The runtime manifest also
records the exact `uv.lock` SHA-256; the release venv is created and smoke-tested in its final immutable directory.
OWNER DEV-only Python tracebacks and native launcher failures remain in `<Desktop>\PackLab\OwnerDev\logs`.

The post-refresh command prints `OWNER_DEV_EXE_READY <full_sha> <runtime_id> <desktop_exe> <launcher_exe>` only after runtime SHA,
canonical icon, EXE hashes, GUI subsystem, Shell icon extraction, Desktop `.lnk` absence, and native Start Menu target
checks pass. The Desktop executable is byte-identical to the stable launcher and never captures a Codex worktree.
This owner-local source runtime does not satisfy PL-0350 redistribution or PL-0351 clean-install acceptance.

Record the command, exit status, deployed SHA, shortcut paths, and failures in the child task's own Codex log. A local
refresh failure is an owner-local delivery failure; it does not authorize rewriting published commits, modifying the
owner's Desktop checkout, or claiming independent acceptance. Never run the refresh before the task's published
remote parity is verified. The active prompt may explicitly define a different final handoff and takes precedence.

## Boundaries

- `TASKS.md` and ChatGPT audit verdicts remain ChatGPT-owned.
- The runtime is local to the Desktop PackLab project under `OwnerDev` and contains no PackLab project data, Codex logs, tests, credentials,
  or Git metadata.
- Launch uses `pythonw.exe`, does not download or update dependencies, and does not write to repository source.
- Taskbar pinning uses only a legitimate Windows shell verb if one is exposed. Never edit Taskband registry state or
  restart Explorer to force a pin.
- This owner-dev source runtime does not satisfy PL-0350 redistribution or PL-0351 clean-install acceptance.
