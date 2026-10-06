# OWNER-DEV-LAUNCHER - ChatGPT Audit Criteria V01

All criteria mandatory.

1. Exact owner-supplied icon is found by canonical SHA and copied into repository branding assets without substitution.
2. Application/window/frozen EXE icon integration uses the canonical PackLab icon and stable Windows AppUserModelID.
3. Owner-dev launch does not depend on a transient Codex worktree or dirty/stale Desktop checkout.
4. A stable atomic runtime exists at `%LOCALAPPDATA%\PackLab\OwnerDev\current`, built from exact published HEAD with `uv sync --locked`.
5. Failed update leaves the previous known-good owner runtime intact.
6. Desktop and Start Menu `PackLab.lnk` files are recreated deterministically and carry current HEAD SHA in Description plus canonical icon.
7. Launcher uses pythonw/source-mode runtime, leaves no console, performs no runtime download and records startup failure locally.
8. Running PackLab taskbar/window icon is canonical; programmatic pin is attempted only through a legitimate shell verb and Windows restrictions are not bypassed via registry hacks.
9. Post-Codex refresh script updates runtime and shortcuts and emits `OWNER_DEV_READY`; this becomes the standing final owner-local step for future Codex implementations.
10. Production PyInstaller spec also embeds the canonical ICO without bypassing PL-0350/PL-0351.
11. Actual owner-machine validation proves current deployed SHA, both shortcuts and a successful double-click-equivalent PackLab launch.
12. No owner data, absolute owner path, secret, project state or transient worktree identity enters canonical repository artifacts.
13. Focused/static/full tests and privacy/scope checks pass.
14. Implementation/evidence and log publication are distinct; log ends exactly `READY_FOR_INDEPENDENT_AUDIT`.

Prompt:
https://github.com/Sekiph82/PackLab/blob/main/coordination/sessions/M16-C001/OWNER_DEV_LAUNCHER_CODEX_PROMPT_V01.md
