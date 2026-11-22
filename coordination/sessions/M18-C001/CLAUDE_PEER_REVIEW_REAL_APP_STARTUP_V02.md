# CLAUDE_PEER_REVIEW: PR #23 real-app startup fixes - V02 (re-review)

- Reviewer: independent Claude peer reviewer (not the builder or tester; not a CHATGPT_AUDIT or CODEX_PEER_REVIEW)
- Head reviewed: origin/fix/real-app-startup f54a549b150f5b73bb57af0f28b3c16703e41e89. Delta against the V01 head 5c4f9a2a:
  - __main__.py, app.py, project_layout.py
  - test_real_app_startup.py
  - PackLabOwnerLauncher.cs, launch_owner_packlab.ps1
- CI: run 45013813431 = success on f54a549b. I checked this with gh.
- Note: history.py, portability.py and reconstruction_workspace.py were not modified. They get the stricter rules because they call the shared `safe_relative_path`. That is the right single place to fix it.

## Verdict: PASS (security scope F2/F3/M1; UI behaviour of F4/F5/F6/F11 NOT_VERIFIED interactively)

## V01 findings
- **H1 RESOLVED.** I re-ran my V01 repro against f54a549b.
  - `"/<tmp>/ESCAPED.txt"` is now rejected ("absolute, rooted, drive or stream path is forbidden").
  - The tests include a regression test for exactly this call (`test_h1_reviewer_escape_call_is_refused`) and a parametrised rejection list.
  - `path()` again ends with a case-insensitive check that the result stays inside the area (normcase/normpath/commonpath).
- **M1 RESOLVED.** `EXIT_ALREADY_RUNNING = 75` is used consistently in app.py, __main__.py, the C# launcher and the ps1. Exit code 3 (abort()/qFatal) is reported as a failure again.
- **M2 RESOLVED.** Trailing dot/space components are rejected, and so is `:` anywhere, which covers streams and drive-relative paths. Reserved device names are rejected, including superscript digits and CONIN$/CONOUT$.
- **L1 RESOLVED.** A junction on the area folder itself (mklink /J at `export`) is now rejected. A project reached through a junction above its root still opens, which is the F2 goal.

## My own bypass attempts on f54a549b (python -I, real NTFS temp folders)
Rejected:
- `/x`, `\x`
- `\?\C:\x`, `//?/C:/x`, `\.\pipe\x`, `//server/share/x`
- `C:x`, `c:/x`
- `a\..`, `a/../..`, `A/...\x`, `.. \x`, `.../x`, `x.`, `x `, `\u202e..`
- `CoN`, `con.tar.gz`, `Nul `, `lpt\u00b9.txt`, `CONIN$`
- the 8.3 short name of an inner junction (`LONGJU~2`), caught by the lstat check

Accepted, and confirmed to stay inside:
- Mixed separators `a/\/b` collapse to `a\b`.
- Unicode lookalikes (fullwidth `．．` and `／`, `∕`, `‥`, `․․`): Win32 W APIs keep them as literal names. I wrote each one, and realpath stayed inside `working`. No file appeared outside the project.

## LOW (non-blocking)
- `COM0`/`LPT0` are accepted. Windows 11 does not treat them as devices, so this is harmless; listing them would only be belt-and-braces.
- `path()` accepts a name with an embedded NUL byte. The OS call then raises ValueError ("embedded null character"). There is no escape, but `safe_relative_path` could reject it up front.
- The V01 LOW items about the mutex identity (USERNAME rather than the user's SID), the window-handle (HWND) file and log rotation still apply. They are not blocking.
