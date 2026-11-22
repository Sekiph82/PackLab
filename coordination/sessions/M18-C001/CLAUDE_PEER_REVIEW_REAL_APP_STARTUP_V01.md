# CLAUDE_PEER_REVIEW: PR #23 real-app startup fixes (F1-F6, F11, F15) - V01

- Reviewer: independent Claude peer reviewer (not the builder or tester; does not replace CHATGPT_AUDIT or CODEX_PEER_REVIEW)
- Head reviewed: origin/fix/real-app-startup 5c4f9a2a37e0b81ade3a14bf5e87770045929eff, diffed against origin/main
- CI: run 45012119904 "PackLab Windows Python Quality" / "Locked Python quality" = success on head 5c4f9a2a (checked with gh)
- Reviewer's own reproductions: scratch scripts, run with `python -I` against the branch and main copies of project_layout.py

## Verdict: CHANGES_REQUIRED

## HIGH

H1. F2 brings back a path-traversal hole through root-relative paths.
`apps/windows-studio/src/packlab_studio/project_layout.py` `path()` (branch lines ~79-92) together with `safe_relative_path()` (lines 19-27).
On Windows, `Path("/x").is_absolute()` is False because the path has no drive, and `text[1] != ":"`, so `safe_relative_path` accepts `/...` and `\...`.
`area_root / Path("/Users/...")` then becomes `C:\Users\...`. On main, `resolve()` plus `commonpath` rejected this. The branch dropped that check, and the lexical join escapes.
Reproduced: on the branch, `layout.path("working", "/<tmp-dir>/ESCAPED.txt")` wrote ESCAPED.txt outside the project. On main the same call raised "project path escapes its area".
Reachable from project or package content: project.py:379 (`record["artifact_directory"]`), project.py:683, project.py:569, build_model.py:647, portability.py:249-253.
Fix: reject any value with a drive or a root (`PureWindowsPath(value).drive or .root`, or a leading `/`/`\`). Keep a final lexical containment assert, for example `os.path.commonpath` on the `abspath` strings of `area_root` and `candidate`, compared case-insensitively. Add negative tests for `/x`, `\x` and `\server\share`.

## MEDIUM

M1. Exit code 3 is ambiguous. MSVC `abort()` exits with code 3, and Qt `qFatal` calls `abort()` (for example when the platform plugin "windows" is missing).
After this change, `PackLabOwnerLauncher.cs:83`, `launch_owner_packlab.ps1:48` and `__main__.py:70` all report such a native startup crash as success and write no startup-failure diagnostic.
Fix: use an unambiguous code (for example 0xA1 or 75), or have the launcher also check for a fresh instance-window marker or the mutex.

M2. Windows normalises names in ways the lexical check does not cover.
- Components with trailing dots or spaces (`".. "`, `"..."`, `". ."`) are accepted. In my tests they failed with ENOENT or EACCES rather than escaping, but that depends on Win32 behaviour and on `\?\` usage.
- ADS (`a.json:stream`) and reserved device names (`NUL`, `CON.txt`) are accepted. They stay inside the area, but they are not legitimate project names.
Recommend rejecting any component that contains `:`, ends in `.` or a space, or is a reserved device name.

## LOW

L1. The link check runs only on components below the area. A junction at `root/<area>` is not checked. This is the same as main (resolve followed both sides), so it is not a regression; documenting it.
The check is time-of-check/time-of-use (TOCTOU), as main was. 8.3 short names alias the same lstat target, so they are detected.

L2. F3 mutex: the `Local\` prefix is per session, and the name is `sha256(getpass.getuser())`, which comes from the USERNAME environment variable, not the user's security ID (SID).
Another user's session cannot squat it. A process in the same session can, but if it uses a restrictive DACL, `CreateMutexW` returns NULL with access denied, `claim_single_instance` returns 0 and the launch continues (fail-open, so no DoS). The remaining exposure is a squat by a same-session process with a permissive DACL. Prefer the user SID in the name.
`instance-window.txt` holds a raw window handle (HWND). A stale handle that has been reused can focus an unrelated window. Cosmetic.

L3. `studio.log` privacy: no `print` or logging calls in Studio source. The log receives library output, `faulthandler` dumps and uncaught tracebacks, which can contain local paths and user names but no tokens or secrets.
The log lives under `%LOCALAPPDATA%` (per-user ACL). Rotation happens only at startup and keeps one generation, so the log can grow without limit within a session.

L4. Removing `""` from `sys.path` is effective for the launchers' `pythonw -c` bootstrap, where `sys.path[0] == ""`. It stops `Documents\PackLab` from becoming an import root after the `chdir`. Good.

## Not verified
- No interactive real-app check (dialogs, multi-monitor geometry) was run by this reviewer.
- F4/F5/F6/F11 UI behaviour was checked only by reading the code.
