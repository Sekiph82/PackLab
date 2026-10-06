# PackLab OWNER DEV Post-Codex Refresh Policy V01

This is the standing local-delivery procedure established by `OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md`.

## Future PackLab implementation handoff

After an implementation is committed and pushed, and local `HEAD`, `origin/main`, and GitHub `main` are confirmed
equal, the Codex implementation actor runs:

```powershell
tools/dev/post_codex_owner_dev_refresh.ps1 -AllowPublishedCommit
```

The script builds a new runtime from that exact clean published commit, runs locked dependency sync and a bounded
source-mode smoke before replacing the prior runtime, refreshes the user's Desktop and Start Menu shortcuts, checks
their SHA/icon metadata, and prints `OWNER_DEV_READY <full_sha> <desktop_lnk> <start_menu_lnk>`. The shortcut always
targets the stable `%LOCALAPPDATA%\PackLab\OwnerDev\current` runtime model; it must never capture a Codex worktree.

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
