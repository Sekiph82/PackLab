# PackLab | Claude Code Local Access & Startup (Windows 11)

This file provides instructions, **not** account credentials or a second task tracker. All user interface/menu labels are in English.

## Required local capabilities
- Claude Code CLI or supported Claude Code Desktop session with access to local workspace `C:\Users\sekip\Desktop\PackLab`.
- Git client able to fetch/push `Sekiph82/PackLab` and an authenticated write-capable GitHub identity. Confirm with `git remote -v` and `gh auth status` if GitHub CLI is installed.
- The project's `.claude/settings.json` supplies scoped permissions after trust; personal and organizational settings take precedence where applicable. It does not supply tokens or sidestep OS permissions.
- Optional platforms: local Windows Python, PySide6, Qt, COLMAP/OpenMVS/Open3D/OCCT and Blender as actually installed; hosted GitHub Actions macOS for Xcode/XCTest. Do NOT attempt Windows Xcode or require broken Android Emulator.
- The repository currently reports PUBLIC. No confidential scan, Apple signing material or supplier data in Git.

## First local read-only preflight
Open a PowerShell terminal on Windows:

```powershell
Set-Location "C:\Users\sekip\Desktop\PackLab"
git status --short
git remote -v
git branch --show-current
git rev-parse HEAD
git fetch origin main
git rev-parse origin/main
gh auth status
claude --version
```

If `gh` is absent, use Git authentication directly; GitHub CLI is optional unless task automation needs its workflow commands. If Claude CLI is not installed/signed in, install/sign in using the official Claude Code process. Never paste credentials into chat, commits or logs.

## Safe sync
If the owner Desktop checkout is clean, on `main`, and its history is safely fast-forwardable, run `git pull --ff-only origin main`. If it has dirty tracked/untracked owner files or diverged commits, do NOT reset, clean, force-push, blindly stash or delete anything; let Claude inspect/resolve a safe non-destructive path. Verify local and `origin/main` SHA equality before claiming sync.

For subsequent accepted tasks, use `tools/dev/post_task_safe_sync.ps1` and report actual parity or `LOCAL_SYNC_PENDING` (do not force an unsafe sync).

## Start Claude
Run `claude` from the PackLab repo root and instruct it: "Read CLAUDE.md and coordination/AUTONOMOUS_CLAUDE_GOAL.md. Own all unfinished PL tasks. Start from current TASKS.md without rerunning completed work."

The project config permits routine edits and selected Git/CI commands but does not guarantee all actions can run without a prompt. Workspace trust, managed rules, external permission checks and genuine device/signing/legal requirements still apply. Claude Code runs within active session limits; no background daemon was installed by this handoff.
